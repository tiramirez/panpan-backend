import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/shared"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambdas/api"))


def test_update_products_list(s3_bucket):
    from routes.update_products import update_products
    result = update_products({
        "file": "products_list",
        "content": [{"name": "Apples", "price": 3.0, "unit": "each"}],
    })
    assert result["message"] == "Successful POST Execution"


def test_update_newsletter(s3_bucket):
    from routes.update_products import update_products
    result = update_products({
        "file": "newsletter",
        "content": "This week's newsletter",
    })
    assert result["message"] == "Successful POST Execution"
