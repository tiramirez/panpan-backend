import json
import os
import uuid
from datetime import datetime, timezone

UTC = timezone.utc

import boto3
from fastapi import APIRouter
from pydantic import BaseModel

from shared.s3 import read_json
from shared.logger import get_logger, log_event

router = APIRouter()
logger = get_logger(__name__)


class CheckoutRequest(BaseModel):
    class Config:
        extra = "allow"


@router.post("/checkout")
def checkout(body: dict):
    try:
        bucket = os.environ["PANPAN_BUCKET_NAME"]
        queue_url = os.environ["PANPAN_QUEUE_URL"]

        s3 = boto3.client("s3")
        newsletter = read_json(s3, bucket, "newsletter.json")
        update_str = newsletter.get("updated_at")
        updated_at = datetime.fromisoformat(update_str + "+00:00")
        now = datetime.now(tz=UTC)
        days_since_update = (now - updated_at).days

        if days_since_update > 3:
            logger.info("Store is closed (newsletter last updated %d days ago)", days_since_update)
            log_event(logger, "checkout_rejected", days_since_update=days_since_update)
            return {
                "message": "Successful POST Execution",
                "title": "We are closed",
                "body": "We open on Monday at 17:00 and close on Thursdays at 18:00",
            }

        order_id = str(uuid.uuid4())
        sqs = boto3.client("sqs")
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                "order_id": order_id,
                "order": body,
                "menu_version": update_str,
            }),
        )

        logger.info("Order %s queued successfully", order_id)
        log_event(logger, "checkout_completed", order_id=order_id, product_count=len(body.get("products", [])), menu_version=update_str)
        return {
            "message": "Successful POST Execution",
            "title": "Congratulations!",
            "body": f"We received your order #{str(order_id)[:6].upper()}. Thank you for placing an order with Pan Pan. A confirmation email will be sent to the email address you provided.",
        }
    except Exception as e:
        logger.exception("Checkout error: %s", e)
        log_event(logger, "checkout_error", error_type=type(e).__name__)
        return {
            "message": "ERROR POST Execution",
            "title": "We are sorry! :(",
            "body": "Please, try again later. If the error persists email us at pandemicpantrywest@gmail.com.",
            "details": str(e),
        }
