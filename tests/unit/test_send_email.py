import sys
import os
import importlib.util
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/shared"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/send-email"))

from unittest.mock import patch, MagicMock


def _import_send_email_handler():
    handler_path = os.path.join(os.path.dirname(__file__), "../../lambdas/send-email/handler.py")
    spec = importlib.util.spec_from_file_location("send_email_handler", handler_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_sqs_event(order_id="abc123", email="test@example.com"):
    import json
    return {
        "Records": [{
            "body": json.dumps({
                "order_id": order_id,
                "menu_version": "2026-06-12",
                "order": {
                    "email": email,
                    "phone": "555-0000",
                    "firstName": "Jane",
                    "lastName": "Doe",
                    "comments": "",
                    "donation": "2.00",
                    "products": [
                        {"product_name": "Apples", "product_quantity": 2, "unit_price": 3.0}
                    ],
                },
            })
        }]
    }


def test_handler_success(dynamodb_table):
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__ = MagicMock()
        mock_smtp.return_value.sendmail = MagicMock(return_value={})
        mock_smtp.return_value.quit = MagicMock()
        mock_smtp.return_value.ehlo = MagicMock()
        mock_smtp.return_value.starttls = MagicMock()
        mock_smtp.return_value.login = MagicMock()

        handler = _import_send_email_handler()
        result = handler.lambda_handler(make_sqs_event(), {})
        assert result["statusCode"] == 200
