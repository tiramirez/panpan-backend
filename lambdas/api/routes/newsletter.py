import os

import boto3
from fastapi import APIRouter

from shared.s3 import read_json
from shared.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/newsletter")
def get_newsletter():
    try:
        bucket = os.environ["PANPAN_BUCKET_NAME"]
        s3 = boto3.client("s3")
        data = read_json(s3, bucket, "newsletter.json")
        return {"ok": True, "data": data}
    except Exception as e:
        logger.error(f"Error fetching newsletter: {e}")
        return {"ok": False, "error": str(e)}
