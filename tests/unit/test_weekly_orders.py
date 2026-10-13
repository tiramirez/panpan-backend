import sys
import os
import json
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/shared"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/api"))


EXPECTED_OUTPUT = {
    "data": {
        "created_at": {
            "0": "2026-08-10 21:24:59",
            "1": "2026-08-10 21:14:01",
        },
        "email": {
            "0": "john.doe@gmail.com",
            "1": "john.doe+1@gmail.com",
        },
        "Crushed Tomatoes - $5.55 per 28oz can": {"0": 1, "1": 1},
        "Cantaloupe - $5.55 each": {"0": 1, "1": ""},
    }
}

SAMPLE_CATALOG = {  ## LEGACY CATALOG
    "data": {
        "Items": [
            {
                "name": "Cantaloupe",
                "unit": "each",
                "price": 3.25,
                "category": "Produce",
            },
            {
                "name": "Crushed Tomatoes",
                "unit": "28oz can",
                "price": 5.55,
                "category": "Produce",
            },
        ],
        "updated_at": "2026-07-21T15:52:10.899511",
        "expries_at": "2026-07-26T15:52:10.899511",
    }
}


SAMPLE_ORDERS = {
    "Items": [
        {
            "created_at": "2026-08-10 21:24:59",
            "email": "john.doe@gmail.com",
            "firstName": "John",
            "lastName": "Doe",
            "phone": "+1234567890",
            "comments": "",
            "donation": 1,
            "menu_version": "ABC",
            "tip": 0,
            "products": [
                {
                    "id": "Cantaloupe",
                    "product_category": "Produce",
                    "product_name": "Cantaloupe",
                    "product_quantity": 1,
                    "product_unit": "each",
                    "unit_price": 3.25,
                },
                {
                    "id": "Crushed Tomatoes",
                    "product_category": "Produce",
                    "product_name": "Crushed Tomatoes",
                    "product_quantity": 1,
                    "product_unit": "28oz can",
                    "unit_price": 5.55,
                },
            ],
        },
        {
            "created_at": "2026-08-10 21:14:01",
            "email": "john.doe+1@gmail.com",
            "firstName": "John",
            "lastName": "Doe",
            "phone": "+1234567890",
            "comments": "",
            "donation": 0,
            "menu_version": "ABC",
            "tip": 0,
            "products": [
                {
                    "id": "Cantaloupe",
                    "product_category": "Produce",
                    "product_name": "Cantaloupe",
                    "product_quantity": 1,
                    "product_unit": "each",
                    "unit_price": 3.25,
                }
            ],
        },
    ]
}


def seed_order(dynamodb_table, week: str, order_id: str, email: str, products: list):
    dynamodb_table.put_item(
        Item={
            "PK": week,
            "SK": f"o#{order_id}",
            "entity_type": "order",
            "created_at": "2026-06-20T12:00:00",
            "menu_version": "2026-25",
            "email": email,
            "phone": "555-0000",
            "firstName": "Jane",
            "lastName": "Doe",
            "comments": "",
            "donation": "2.00",
            "products": products,
        }
    )


def test_weekly_orders_empty_week(s3_bucket, dynamodb_table):
    s3_bucket.put_object(
        Bucket="panpan-test-content",
        Key="products_list.json",
        Body=json.dumps(
            {"Items": [{"name": "Apples", "price": 3.0, "unit": "each"}]}
        ).encode(),
    )

    from routes.weekly_orders import weekly_orders

    result = weekly_orders(week="2026-25")
    assert "ok" in result
    assert result["ok"] is True


def test_weekly_orders_returns_pivot(s3_bucket, dynamodb_table):
    s3_bucket.put_object(
        Bucket="panpan-test-content",
        Key="products_list.json",
        Body=json.dumps(
            {
                "Items": [
                    {"name": "Apples", "price": 3.0, "unit": "each"},
                    {"name": "Oranges", "price": 2.0, "unit": "each"},
                ]
            }
        ).encode(),
    )

    seed_order(
        dynamodb_table,
        "2026-25",
        "order-001",
        "alice@example.com",
        [
            {
                "product_name": "Apples",
                "product_quantity": 2,
                "unit_price": Decimal("3.00"),
            },
            {
                "product_name": "Oranges",
                "product_quantity": 1,
                "unit_price": Decimal("2.00"),
            },
        ],
    )
    seed_order(
        dynamodb_table,
        "2026-25",
        "order-002",
        "bob@example.com",
        [
            {
                "product_name": "Apples",
                "product_quantity": 3,
                "unit_price": Decimal("3.00"),
            },
        ],
    )

    from routes.weekly_orders import weekly_orders

    result = weekly_orders(week="2026-25")

    assert result.get("ok") is True
    data = result["data"]

    # Both orders should appear as rows
    emails = list(data.get("email", {}).values())
    assert "alice@example.com" in emails
    assert "bob@example.com" in emails

    # Apples column should exist (renamed to long name by column_names_dict)
    apples_col = "Apples - $3.00 each"
    assert (
        apples_col in data
    ), f"Expected '{apples_col}' in data keys: {list(data.keys())}"

    # Check Alice has 2 apples and Bob has 3
    order_idx = {v: k for k, v in data["email"].items()}
    alice_idx = order_idx["alice@example.com"]
    bob_idx = order_idx["bob@example.com"]
    assert data[apples_col][alice_idx] == 2
    assert data[apples_col][bob_idx] == 3


def test_weekly_orders_different_weeks_isolated(s3_bucket, dynamodb_table):
    s3_bucket.put_object(
        Bucket="panpan-test-content",
        Key="products_list.json",
        Body=json.dumps(
            {"Items": [{"name": "Apples", "price": 3.0, "unit": "each"}]}
        ).encode(),
    )

    seed_order(
        dynamodb_table,
        "2026-25",
        "order-w25",
        "w25@example.com",
        [
            {
                "product_name": "Apples",
                "product_quantity": 1,
                "unit_price": Decimal("3.00"),
            },
        ],
    )
    seed_order(
        dynamodb_table,
        "2026-26",
        "order-w26",
        "w26@example.com",
        [
            {
                "product_name": "Apples",
                "product_quantity": 2,
                "unit_price": Decimal("3.00"),
            },
        ],
    )

    from routes.weekly_orders import weekly_orders

    result = weekly_orders(week="2026-25")
    assert result.get("ok") is True
    emails = list(result["data"].get("email", {}).values())
    assert "w25@example.com" in emails
    assert "w26@example.com" not in emails
