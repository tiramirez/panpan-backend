import os
import re
import smtplib
from email.message import EmailMessage

from shared.logger import get_logger, log_event

logger = get_logger()


def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    return re.sub(r"[  -​]", " ", text)


def email_body_template(order_id, order_subtotal, donation, service_fee, str_products):
    return f"""
Hi there,
Thank you for placing an order with Pan Pan.
Your order ID is #{order_id.upper()}. Below is a copy of the order we received.

For support with your order or for any questions, email us at pandemicpantrywest@gmail.com.
You can pick up your share at 705 S 50th Street, Philadelphia, PA during our weekly pick up windows:
    * Friday from 3PM to 7PM
    * Saturday from 11AM to 2PM

See you later this week!

- The Pan Pan Team
-------------------------
Order details:
{str_products}
-------------------------
SUBTOTAL: ${float(order_subtotal):.2f}
DONATION: ${float(donation):.2f}
SERVICE FEE: ${float(service_fee):.2f}
-------------------------
TOTAL: ${float(order_subtotal) + float(donation) + float(service_fee):.2f}
""".strip()


def send_email(email, order_id, order_subtotal, donation, service_fee, str_products, cc=None):
    cc = [a for a in (cc or []) if a]
    logger.info(f"Sending confirmation email to {email}, cc={cc}, order {order_id}")

    email = clean_text(email)
    order_id = clean_text(order_id)
    str_products = clean_text(str_products)
    body = clean_text(email_body_template(order_id, order_subtotal, donation, service_fee, str_products))

    msg = EmailMessage()
    msg["From"] = "Pandemic Pantry <pandemicpantrywest@gmail.com>"
    msg["To"] = email
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = f"Your order was received: {order_id.upper()}"
    msg.set_payload(body, charset="utf-8")

    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.ehlo()
    smtp.starttls()
    gmail_username = os.environ.get("PANPAN_FROM_EMAIL", "pandemicpantrywest@gmail.com")
    gmail_password = os.environ["PANPAN_GMAIL_PASSWORD"]
    smtp.login(gmail_username, gmail_password)
    try:
        status = smtp.sendmail(msg["From"], [email] + cc, msg.as_string())
        log_event(logger, "email_sent", order_id=order_id, email_domain=email.split("@")[-1])
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        log_event(logger, "email_failed", order_id=order_id, error_type=type(e).__name__)
        status = None
    logger.info(f"sendmail_status: {status}")
    smtp.quit()
