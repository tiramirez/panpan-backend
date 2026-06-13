import os
import datetime as dt
import hashlib
import uuid
from decimal import Decimal

import boto3
import pandas as pd

from logger import get_logger

logger = get_logger()


def save_order(order_id: str, order: dict, **kwargs):
    logger.info(f"Saving order #{order_id}")

    email = order.get("email")
    phone = order.get("phone")
    first_name = order.get("firstName", "")
    last_name = order.get("lastName", "")
    comments = order.get("comments", "")
    donation = order.get("donation")
    service_fee = 4.0
    products = order.get("products")

    df = pd.DataFrame(products)
    order_total = df.assign(subtotal=df.product_quantity * df.unit_price).subtotal.sum()
    date_str = dt.datetime.now().isoformat()
    week_str = dt.datetime.now().strftime("%G-%V")

    table_name = os.environ["PANPAN_TABLE_NAME"]
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    table.put_item(Item={
        "PK": f"o#{order_id}",
        "SK": f"u#{email}",
        "entity_type": "order",
        "week_str": week_str,
        "created_at": date_str,
        "donation": str(donation),
        "products_total": Decimal(str(order_total)),
        "service_fee": Decimal(str(service_fee)),
        "comments": comments,
        "GSI2-PK": week_str,
        "GSI2-SK": f"o#{order_id}",
    })
    logger.info("Saved order details")

    with table.batch_writer() as batch:
        for i in range(df.shape[0]):
            product_id = uuid.UUID(hex=hashlib.shake_128(
                bytes(df.product_name[i], encoding="utf-8")
            ).hexdigest(16))
            batch.put_item(Item={
                "PK": f"o#{order_id}",
                "SK": f"p#{product_id}",
                "entity_type": "order_product",
                "product_name": df.product_name[i],
                "product_quantity": str(df.product_quantity[i]),
                "unit_price": Decimal(str(df.unit_price[i])),
                "email": f"u#{email}",
                "phone": f"u#{phone}",
                "firstName": f"u#{first_name}",
                "lastName": f"u#{last_name}",
                "GSI1-PK": week_str,
                "GSI1-SK": f"o#{order_id}#p#{product_id}",
            })
    logger.info("Saved order products")
