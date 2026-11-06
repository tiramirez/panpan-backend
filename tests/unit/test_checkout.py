import json
import sys
import os
import pytest
from datetime import datetime, timezone, timedelta

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


def _updated_at(days_ago):
    return (datetime.now(tz=timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%S")


def test_checkout_success(s3_bucket, sqs_queue):
    s3_bucket.put_object(
        Bucket="panpan-test-content",
        Key="newsletter.json",
        Body=json.dumps({"updated_at": _updated_at(1)}).encode(),
    )

    from routes.checkout import checkout
    result = checkout(make_checkout_body())
    assert result["title"] == "Congratulations!"


def test_checkout_closed(s3_bucket, sqs_queue):
    s3_bucket.put_object(
        Bucket="panpan-test-content",
        Key="newsletter.json",
        Body=json.dumps({"updated_at": _updated_at(5)}).encode(),
    )

    from routes.checkout import checkout
    result = checkout(make_checkout_body())
    assert result["title"] == "We are closed"


def _queued_order_id(sqs):
    queue_url = os.environ["PANPAN_QUEUE_URL"]
    msg = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)["Messages"][0]
    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"])
    return json.loads(msg["Body"])["order_id"]


def test_checkout_uses_checkout_id_as_order_id(s3_bucket, sqs_queue):
    s3_bucket.put_object(
        Bucket="panpan-test-content",
        Key="newsletter.json",
        Body=json.dumps({"updated_at": _updated_at(1)}).encode(),
    )
    checkout_id = "3f2b8c1e-9d4a-4e6b-8f1a-2c3d4e5f6a7b"

    from routes.checkout import checkout
    result = checkout({**make_checkout_body(), "checkout_id": checkout_id})
    assert result["title"] == "Congratulations!"
    assert _queued_order_id(sqs_queue) == checkout_id


@pytest.mark.parametrize("checkout_id", [None, "", "not-a-uuid", 123])
def test_checkout_invalid_checkout_id_gets_new_uuid(s3_bucket, sqs_queue, checkout_id):
    import uuid
    s3_bucket.put_object(
        Bucket="panpan-test-content",
        Key="newsletter.json",
        Body=json.dumps({"updated_at": _updated_at(1)}).encode(),
    )

    from routes.checkout import checkout
    checkout({**make_checkout_body(), "checkout_id": checkout_id})
    uuid.UUID(_queued_order_id(sqs_queue))
