import json
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/shared"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/api"))

from unittest.mock import patch, MagicMock


def make_checkout_body():
    return {
        "email": "test@example.com",
        "firstName": "Jane",
        "lastName": "Doe",
        "phone": "555-1234",
        "comments": "",
        "donation": "2.00",
        "products": [
            {"product_name": "Apples", "product_quantity": 2, "unit_price": 3.0}
        ],
    }


def test_checkout_success(s3_bucket, sqs_queue):
    import json
    s3_bucket.put_object(
        Bucket="panpan-test-content",
        Key="newsletter.json",
        Body=json.dumps({"updated_at": "2026-06-12T10:00:00"}).encode(),
    )

    from routes.checkout import checkout
    result = checkout(make_checkout_body())
    assert result["title"] == "Congratulations!"


def test_checkout_closed(s3_bucket, sqs_queue):
    import json
    s3_bucket.put_object(
        Bucket="panpan-test-content",
        Key="newsletter.json",
        Body=json.dumps({"updated_at": "2026-06-01T10:00:00"}).encode(),
    )

    from routes.checkout import checkout
    result = checkout(make_checkout_body())
    assert result["title"] == "We are closed"
