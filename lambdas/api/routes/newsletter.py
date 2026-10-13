import os

from boto3 import client
from fastapi import APIRouter

from shared.s3 import read_json
from shared.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/newsletter")
def get_newsletter():
    try:
        bucket = os.environ["PANPAN_BUCKET_NAME"]
        s3 = client("s3")
        data = read_json(s3, bucket, "newsletter.json")
        logger.info("Fetched newsletter (updated_at=%s)", data.get("updated_at"))
        return {"ok": True, "data": data}
    except Exception as e:
        logger.exception("Error fetching newsletter: %s", e)
        return {"ok": False, "error": str(e)}
