import os
import pytest
import boto3
from moto import mock_aws

os.environ.setdefault("PANPAN_ENV", "test")
os.environ.setdefault("PANPAN_TABLE_NAME", "panpan-test-orders")
os.environ.setdefault("PANPAN_BUCKET_NAME", "panpan-test-content")
os.environ.setdefault("PANPAN_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456789012/panpan-test-orders")
os.environ.setdefault("PANPAN_FROM_EMAIL", "test@example.com")
os.environ.setdefault("PANPAN_GMAIL_PASSWORD", "test-password")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")


@pytest.fixture
def aws_mock():
    with mock_aws():
        yield


@pytest.fixture
def dynamodb_table(aws_mock):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.create_table(
        TableName="panpan-test-orders",
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
            {"AttributeName": "GSI1-PK", "AttributeType": "S"},
            {"AttributeName": "GSI1-SK", "AttributeType": "S"},
            {"AttributeName": "GSI2-PK", "AttributeType": "S"},
            {"AttributeName": "GSI2-SK", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1-PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1-SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "GSI2",
                "KeySchema": [
                    {"AttributeName": "GSI2-PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI2-SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    return table


@pytest.fixture
def s3_bucket(aws_mock):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="panpan-test-content")
    return s3


@pytest.fixture
def sqs_queue(aws_mock):
    sqs = boto3.client("sqs", region_name="us-east-1")
    response = sqs.create_queue(QueueName="panpan-test-orders")
    os.environ["PANPAN_QUEUE_URL"] = response["QueueUrl"]
    return sqs
