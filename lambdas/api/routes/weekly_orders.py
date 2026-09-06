import os

from boto3 import client, resource
from boto3.dynamodb.conditions import Key
from fastapi import APIRouter

from shared.dynamo import query_with_pagination
from shared.s3 import read_json
from shared.logger import get_logger, log_event

router = APIRouter()
logger = get_logger(__name__)


def get_long_name(row):
    if row['unit'] == "each":
        return f"{row['name']} - ${row['price']:.2f} each"
    return f"{row['name']} - ${row['price']:.2f} per {row['unit']}"


@router.get("/weekly-orders")
def weekly_orders(week: str):
    try:
        bucket = os.environ["PANPAN_BUCKET_NAME"]
        table_name = os.environ["PANPAN_TABLE_NAME"]

        ## LOAD FROM ORDERS
        dynamodb = resource("dynamodb")
        table = dynamodb.Table(table_name)

        items = query_with_pagination(table, {
            "KeyConditionExpression": Key("PK").eq(str(week)) & Key("SK").begins_with("o#"),
        })

        if not items:
            return {"ok": True, "data": {}, "message":"No orders this week"}

        ## LOAD CATALOG
        s3 = client("s3")
        catalog = read_json(s3, bucket, "products_list.json")
        products_list = catalog.get("Items",[])

        orders_information = ["order_id", "created_at", "menu_version", "email", "firstName", "lastName", "phone", "comments", "donation"]

        results = {column_name:{} for column_name in orders_information}


        # Explode embedded products into one row per order+product for pivot
        for id, item in enumerate(items):
            sk = item.get("SK", "")
            results["created_at"][id] = item.get("created_at", "")
            results["order_id"][id] = sk[2:] if sk.startswith("o#") else sk
            results["email"][id] = item.get("email", "")
            results["firstName"][id] = item.get("firstName", "")
            results["lastName"][id] = item.get("lastName", "")
            results["phone"][id] = item.get("phone", "")
            results["comments"][id] = item.get("comments", "")
            results["donation"][id] = item.get("donation", "")
            results["menu_version"][id] = item.get("menu_version", "")

            if "tip" in item:
                if "tip" not in results:
                    results["tip"] = {prev_id: "" for prev_id in range(id)}
                results["tip"][id] = item.get("tip", "")
            elif "tip" in results:
                results["tip"][id] = ""

            ## TODO: convert from UTC to US/Eastern 

            order_product_names = {p["product_name"]:p for p in item.get("products", [])}
            for product in products_list:
                long_name = get_long_name(product)
                product_name = product.get("name","")

                if long_name not in results:
                    results[long_name] = {}

                if product_name in order_product_names.keys():
                    results[long_name][id] = order_product_names.get(product_name,{}).get("product_quantity","")
                else:
                    results[long_name][id] = ""


        order_count = len(items)
        log_event(logger, "weekly_orders_queried", week=week, order_count=order_count)

        return {"ok": True, "data": results}

    except Exception as e:
        logger.exception("Error in weekly_orders: %s", e)
        return {"ok": False, "error": "Error processing weekly orders", "details": str(e)}
