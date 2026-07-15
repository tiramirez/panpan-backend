import json

import confirmation_email
import process_order
from shared.logger import get_logger

logger = get_logger(__name__)


def lambda_handler(event, _context):
    try:
        body = event["Records"][0]["body"]
        if isinstance(body, str):
            request = json.loads(body)
        else:
            request = body

        order_id = request.get("order_id")
        order = request.get("order")
        short_id = str(order_id)[:6]
        email = order.get("email")
        products = order.get("products")

        logger.info(f"Processing order #{short_id}")
        process_order.save_order(**request)

        service_fee = 4.0
        subtotal = 0.0
        str_products = ""
        for product in products:
            str_products += f"* ({product.get('product_quantity')} x ${float(product.get('unit_price')):5.2f}) - {product.get('product_name')}\n"
            subtotal += float(product.get("unit_price")) * float(product.get("product_quantity"))

        additional_emails = order.get("additionalEmails", [])
        confirmation_email.send_email(
            email=email,
            order_id=short_id,
            order_subtotal=str(subtotal),
            donation=order.get("donation"),
            service_fee=service_fee,
            str_products=str_products,
            cc=additional_emails,
        )
        logger.info(f"Confirmation email sent to: {email}, cc={additional_emails}")

        return {"statusCode": 200, "body": json.dumps(f"Confirmation email sent. Order ID {short_id}")}

    except Exception as e:
        logger.error(f"Error: {e}")
        return {"statusCode": 500, "body": json.dumps("ERROR POST Execution")}
