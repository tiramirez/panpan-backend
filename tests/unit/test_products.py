import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/shared"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/api"))

_FUTURE = "2027-01-01T00:00:00+00:00"


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


def test_get_products_with_experiment(s3_bucket, dynamodb_table):
    exp_id = "exp-abc"
    os.environ["PANPAN_ACTIVE_EXPERIMENTS"] = json.dumps([{
        "id": exp_id, "variants": ["a", "b"], "expires_at": _FUTURE,
    }])
    for variant in ["a", "b"]:
        s3_bucket.put_object(
            Bucket="panpan-test-content",
            Key=f"experiments/products_list_{exp_id}_{variant}.json",
            Body=json.dumps({
                "Items": [{"name": f"Variant {variant}", "price": 1.0, "unit": "each"}],
                "updated_at": "2026-07-14T10:00:00",
            }).encode(),
        )
    try:
        from routes.products import get_products
        result = get_products(did="device-123")
        assert result["ok"] is True
        assert result["experiment"]["id"] == exp_id
        assert result["experiment"]["variant"] in ("a", "b")
        assert result["data"]["Items"][0]["name"].startswith("Variant ")
    finally:
        del os.environ["PANPAN_ACTIVE_EXPERIMENTS"]


def test_get_products_variant_failure_falls_back(s3_bucket):
    # No DynamoDB table → _assign_variant raises → fallback to products_list.json
    exp_id = "exp-xyz"
    os.environ["PANPAN_ACTIVE_EXPERIMENTS"] = json.dumps([{
        "id": exp_id, "variants": ["a", "b"], "expires_at": _FUTURE,
    }])
    s3_bucket.put_object(
        Bucket="panpan-test-content",
        Key="products_list.json",
        Body=json.dumps({
            "Items": [{"name": "Fallback Product", "price": 2.0, "unit": "each"}],
            "updated_at": "2026-07-14T10:00:00",
        }).encode(),
    )
    try:
        from routes.products import get_products
        result = get_products(did="device-123")
        assert result["ok"] is True
        assert result["data"]["Items"][0]["name"] == "Fallback Product"
    finally:
        del os.environ["PANPAN_ACTIVE_EXPERIMENTS"]
