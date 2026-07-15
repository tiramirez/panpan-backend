import sys
import os
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/shared"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/send-email"))


def make_order(**overrides):
    base = {
        "email": "test@example.com",
        "phone": "555-0000",
        "firstName": "Jane",
        "lastName": "Doe",
        "comments": "no onions",
        "donation": "2.00",
        "products": [
            {"product_name": "Apples", "product_quantity": 2, "unit_price": 3.0},
            {"product_name": "Oranges", "product_quantity": 1, "unit_price": 2.0},
        ],
    }
    base.update(overrides)
    return base


def test_save_order_single_item_written(dynamodb_table):
    from process_order import save_order

    save_order("order-001", make_order(), menu_version="2026-25")

    # Table should contain exactly one item for this order
    resp = dynamodb_table.scan()
    items = resp["Items"]
    assert len(items) == 1


def test_save_order_item_structure(dynamodb_table):
    from process_order import save_order
    import datetime as dt

    save_order("order-abc", make_order(), menu_version="2026-25")

    resp = dynamodb_table.scan()
    item = resp["Items"][0]

    week_str = dt.datetime.now().strftime("%G-%V")

    assert item["PK"] == week_str
    assert item["SK"] == "o#order-abc"
    assert item["entity_type"] == "order"
    assert item["email"] == "test@example.com"
    assert item["phone"] == "555-0000"
    assert item["firstName"] == "Jane"
    assert item["lastName"] == "Doe"
    assert item["comments"] == "no onions"
    assert item["donation"] == "2.00"
    assert item["menu_version"] == "2026-25"

    # GSI attributes must NOT be present
    assert "GSI1-PK" not in item
    assert "GSI2-PK" not in item
    assert "GSI1-SK" not in item
    assert "GSI2-SK" not in item


def test_save_order_products_embedded(dynamodb_table):
    from process_order import save_order

    save_order("order-emb", make_order(), menu_version="2026-25")

    item = dynamodb_table.scan()["Items"][0]
    products = item["products"]

    assert isinstance(products, list)
    assert len(products) == 2

    apples = next(p for p in products if p["product_name"] == "Apples")
    assert apples["product_quantity"] == 2
    assert apples["unit_price"] == Decimal("3.0")

    oranges = next(p for p in products if p["product_name"] == "Oranges")
    assert oranges["product_quantity"] == 1
    assert oranges["unit_price"] == Decimal("2.0")


def test_save_order_total_computed(dynamodb_table):
    from process_order import save_order

    save_order("order-total", make_order(), menu_version="2026-25")

    item = dynamodb_table.scan()["Items"][0]
    # 2 * 3.0 + 1 * 2.0 = 8.0
    assert item["products_total"] == Decimal("8.0")


def test_save_order_menu_version_default_empty(dynamodb_table):
    from process_order import save_order

    save_order("order-noversion", make_order())

    item = dynamodb_table.scan()["Items"][0]
    assert item["menu_version"] == ""


def test_save_order_no_u_prefix_on_fields(dynamodb_table):
    from process_order import save_order

    save_order("order-prefix", make_order())

    item = dynamodb_table.scan()["Items"][0]
    assert not item["email"].startswith("u#")
    assert not item["phone"].startswith("u#")
    assert not item["firstName"].startswith("u#")
    assert not item["lastName"].startswith("u#")
