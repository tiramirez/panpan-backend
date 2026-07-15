import json
import sys
import os
import pytest
from datetime import datetime, timezone, timedelta

UTC = timezone.utc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/shared"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/api"))


def test_checkout_writes_to_sqs(s3_bucket, sqs_queue):
    import boto3
    s3_bucket.put_object(
        Bucket="panpan-test-content",
        Key="newsletter.json",
        Body=json.dumps({"updated_at": datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%S")}).encode(),
    )

    from routes.checkout import checkout
    result = checkout({
        "email": "test@example.com",
        "firstName": "Jane",
        "lastName": "Doe",
        "phone": "555-1234",
        "comments": "",
        "donation": "2.00",
        "products": [
            {"product_name": "Apples", "product_quantity": 2, "unit_price": 3.0}
        ],
    })

    assert result["title"] == "Congratulations!" or result["title"] == "We are closed"

    sqs = boto3.client("sqs", region_name="us-east-1")
    queue_url = os.environ["PANPAN_QUEUE_URL"]
    messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
    assert "Messages" in messages
    body = json.loads(messages["Messages"][0]["Body"])
    assert "order_id" in body
