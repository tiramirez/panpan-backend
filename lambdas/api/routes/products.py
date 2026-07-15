import os

import boto3
from fastapi import APIRouter

from shared.s3 import read_json
from shared.logger import get_logger, log_event

router = APIRouter()
logger = get_logger(__name__)


@router.get("/products")
def get_products():
    try:
        bucket = os.environ["PANPAN_BUCKET_NAME"]
        s3 = boto3.client("s3")
        data = read_json(s3, bucket, "products_list.json")
        product_count = len(data.get("Items", []))
        logger.info("Fetched %d products", product_count)
        log_event(logger, "menu_queried", product_count=product_count)
        return {"ok": True, "data": data}
    except Exception as e:
        logger.exception("Error fetching products: %s", e)
        return {"ok": False, "error": str(e)}
