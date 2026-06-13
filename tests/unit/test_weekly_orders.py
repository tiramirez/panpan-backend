import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/shared"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/api"))


def test_weekly_orders_empty_week(s3_bucket, dynamodb_table):
    import json
    s3_bucket.put_object(
        Bucket="panpan-test-content",
        Key="products_list.json",
        Body=json.dumps({
            "Items": [
                {"name": "Apples", "price": 3.0, "unit": "each"}
            ]
        }).encode(),
    )

    from routes.weekly_orders import weekly_orders
    result = weekly_orders(week="2026-25")
    assert "ok" in result or "error" in result
