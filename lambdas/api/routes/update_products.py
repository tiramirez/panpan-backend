import datetime
import json
import os

import boto3
from fastapi import APIRouter

from shared.s3 import put_bytes
from shared.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/update-products")
def update_products(body: dict):
    try:
        file = body.get("file")
        content = body.get("content")
        bucket = os.environ["PANPAN_BUCKET_NAME"]

        if file == "products_list":
            file_name = "products_list.json"
            data = bytes(json.dumps({
                "Items": content,
                "updated_at": datetime.datetime.now().isoformat(),
            }, indent=2).encode("utf-8"))
        elif file == "newsletter":
            file_name = "newsletter.json"
            data = bytes(json.dumps({
                "Body": content,
                "updated_at": datetime.datetime.now().isoformat(),
            }, indent=2).encode("utf-8"))
        else:
            logger.warning("Unknown file type requested: %s", file)
            return {"error": f"Unknown file type: {file}"}

        s3 = boto3.client("s3")
        put_bytes(s3, bucket, file_name, data)
        logger.info("Updated %s in bucket %s", file_name, bucket)
        return {"message": "Successful POST Execution"}

    except Exception as e:
        logger.exception("Error in update_products: %s", e)
        return {"error": "ERROR POST Execution", "details": str(e)}
