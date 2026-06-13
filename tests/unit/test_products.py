import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/shared"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/api"))


def test_get_products(s3_bucket):
    s3_bucket.put_object(
        Bucket="panpan-test-content",
        Key="products_list.json",
        Body=json.dumps({
            "Items": [{"name": "Apples", "price": 3.0, "unit": "each"}],
            "updated_at": "2026-06-12T10:00:00",
        }).encode(),
    )

    from routes.products import get_products
    result = get_products()
    assert result["ok"] is True
    assert result["data"]["Items"][0]["name"] == "Apples"


def test_get_products_missing_bucket(aws_mock):
    from routes.products import get_products
    result = get_products()
    assert result["ok"] is False
