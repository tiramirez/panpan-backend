import sys
import os
import concurrent.futures
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/shared"))


def update_counter(table, week: str, product_id: str, qty: int):
    table.update_item(
        Key={"PK": week, "SK": f"c#{product_id}"},
        UpdateExpression="ADD qty_sold :delta",
        ExpressionAttributeValues={":delta": Decimal(str(qty))},
    )


def test_counter_item_increments(dynamodb_table):
    week = "2026-27"
    update_counter(dynamodb_table, week, "apples", 2)
    update_counter(dynamodb_table, week, "apples", 3)

    item = dynamodb_table.get_item(Key={"PK": week, "SK": "c#apples"})["Item"]
    assert item["qty_sold"] == Decimal("5")


def test_counter_item_created_on_first_update(dynamodb_table):
    week = "2026-27"
    update_counter(dynamodb_table, week, "oranges", 4)

    resp = dynamodb_table.get_item(Key={"PK": week, "SK": "c#oranges"})
    assert "Item" in resp
    assert resp["Item"]["qty_sold"] == Decimal("4")


def test_counter_items_independent_per_product(dynamodb_table):
    week = "2026-27"
    update_counter(dynamodb_table, week, "apples", 5)
    update_counter(dynamodb_table, week, "oranges", 3)

    apples = dynamodb_table.get_item(Key={"PK": week, "SK": "c#apples"})["Item"]
    oranges = dynamodb_table.get_item(Key={"PK": week, "SK": "c#oranges"})["Item"]

    assert apples["qty_sold"] == Decimal("5")
    assert oranges["qty_sold"] == Decimal("3")


def test_counter_items_query_by_week(dynamodb_table):
    from boto3.dynamodb.conditions import Key

    week = "2026-27"
    update_counter(dynamodb_table, week, "apples", 10)
    update_counter(dynamodb_table, week, "oranges", 7)
    update_counter(dynamodb_table, week, "bananas", 3)

    resp = dynamodb_table.query(
        KeyConditionExpression=Key("PK").eq(week) & Key("SK").begins_with("c#"),
    )
    items = resp["Items"]
    assert len(items) == 3
    total = sum(int(i["qty_sold"]) for i in items)
    assert total == 20


def test_counter_items_concurrent_updates_atomic(dynamodb_table):
    week = "2026-27"

    def increment(n):
        update_counter(dynamodb_table, week, "apples", n)

    # Simulate concurrent increments from 10 "orders"
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(increment, i) for i in range(1, 11)]
        concurrent.futures.wait(futures)

    item = dynamodb_table.get_item(Key={"PK": week, "SK": "c#apples"})["Item"]
    # sum(1..10) = 55
    assert item["qty_sold"] == Decimal("55")
