import os
import datetime as dt
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

from shared.logger import get_logger, log_event

logger = get_logger()


def save_order(order_id: str, order: dict, menu_version: str = "", **kwargs) -> bool:
    """Persist the order. Returns False if an order with this id already exists (duplicate submit)."""
    logger.info(f"Saving order #{order_id}")

    email = order.get("email")
    phone = order.get("phone")
    first_name = order.get("firstName", "")
    last_name = order.get("lastName", "")
    comments = order.get("comments", "")
    donation = order.get("donation")
    service_fee = 4.0
    products = order.get("products")

    products_embedded = [
        {
            "product_name": p["product_name"],
            "product_quantity": int(p["product_quantity"]),
            "unit_price": Decimal(str(p["unit_price"])),
        }
        for p in products
    ]
    order_total = sum(
        p["product_quantity"] * p["unit_price"] for p in products_embedded
    )
    date_str = dt.datetime.now().isoformat()
    week_str = dt.datetime.now().strftime("%G-%V")

    table_name = os.environ["PANPAN_TABLE_NAME"]
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        table.put_item(Item={
            "PK": week_str,
            "SK": f"o#{order_id}",
            "entity_type": "order",
            "created_at": date_str,
            "menu_version": menu_version,
            "email": email,
            "phone": phone,
            "firstName": first_name,
            "lastName": last_name,
            "comments": comments,
            "donation": str(donation),
            "products_total": order_total,
            "service_fee": Decimal(str(service_fee)),
            "products": products_embedded,
            "variant": order.get("variant", "unknown"),
            "device_id": order.get("device_id", "unknown"),
        }, ConditionExpression="attribute_not_exists(SK)")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
        logger.warning("Order #%s already exists, skipping duplicate", order_id)
        log_event(logger, "order_duplicate_skipped", order_id=order_id, week=week_str)
        return False
    logger.info("Saved order with %d embedded products", len(products_embedded))
    log_event(logger, "order_saved", order_id=order_id, week=week_str, product_count=len(products_embedded))
    return True
