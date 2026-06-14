import json
import logging

logger = logging.getLogger(__name__)

def read_json(s3_client, bucket: str, key: str) -> dict:
    try:
        resp = s3_client.get_object(Bucket=bucket, Key=key)
        data = json.loads(resp['Body'].read().decode('utf-8'))
        logger.info(f"Read s3://{bucket}/{key}")
        return data
    except Exception as e:
        logger.error(f"Error reading s3://{bucket}/{key}: {e}")
        raise

def put_bytes(s3_client, bucket: str, key: str, content: bytes) -> None:
    try:
        s3_client.put_object(Body=content, Bucket=bucket, Key=key)
        logger.info(f"Wrote s3://{bucket}/{key}")
    except Exception as e:
        logger.error(f"Error writing s3://{bucket}/{key}: {e}")
        raise
