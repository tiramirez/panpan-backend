import os

import boto3
import pandas as pd
from boto3.dynamodb.conditions import Key
from fastapi import APIRouter

from shared.dynamo import query_with_pagination
from shared.s3 import read_json
from shared.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


def get_long_name(row):
    if row.unit == "each":
        return f"{row['name']} - ${row.price:.2f} each"
    return f"{row['name']} - ${row.price:.2f} per {row.unit}"


@router.get("/weekly-orders")
def weekly_orders(week: str):
    try:
        bucket = os.environ["PANPAN_BUCKET_NAME"]
        table_name = os.environ["PANPAN_TABLE_NAME"]

        s3 = boto3.client("s3")
        json_data = read_json(s3, bucket, "products_list.json")
        products = pd.DataFrame(json_data["Items"])
        column_names_dict = (
            products
            .assign(long_name=products.apply(get_long_name, axis=1))
            .set_index("name")
            .long_name
            .to_dict()
        )

        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

        items = query_with_pagination(table, {
            "KeyConditionExpression": Key("PK").eq(str(week)) & Key("SK").begins_with("o#"),
        })

        new_columns = ["created_at", "menu_version", "email", "firstName", "lastName", "phone", "comments", "donation"] + list(products.name.sort_values().unique())

        if not items:
            return {"ok": True, "data": pd.DataFrame(columns=new_columns).to_dict()}

        # Explode embedded products into one row per order+product for pivot
        rows = []
        for item in items:
            for product in item.get("products", []):
                rows.append({
                    "order_id": item["SK"],
                    "email": item.get("email", ""),
                    "firstName": item.get("firstName", ""),
                    "lastName": item.get("lastName", ""),
                    "phone": item.get("phone", ""),
                    "product_name": product["product_name"],
                    "product_quantity": product["product_quantity"],
                })

        orders = pd.DataFrame(rows)
        df = (
            orders
            .pivot_table(
                index=["order_id", "email", "firstName", "lastName", "phone"],
                columns="product_name",
                aggfunc={"product_quantity": "sum"},
            )
            .product_quantity
            .reset_index()
            .fillna("")
        )

        item_df = pd.DataFrame(items).set_index("SK")
        for col in ["created_at", "donation", "comments", "menu_version"]:
            df[col] = df["order_id"].map(item_df.get(col, pd.Series(dtype=str)).to_dict())

        if "tip" in item_df.columns:
            df["tip"] = df["order_id"].map(item_df["tip"].to_dict())
            new_columns = ["created_at", "menu_version", "email", "firstName", "lastName", "phone", "comments", "donation", "tip"] + list(products.name.sort_values().unique())

        df = pd.concat([pd.DataFrame(columns=new_columns), df])
        df = df.rename(columns=column_names_dict)
        df["created_at"] = (
            pd.to_datetime(df.created_at)
            .dt.tz_localize("UTC")
            .dt.tz_convert("US/Eastern")
            .dt.strftime("%Y-%m-%d %H:%M:%S")
            .astype(str)
        )

        logger.info("Returning weekly orders for week %s: %d rows", week, len(df))
        return {"ok": True, "data": df.fillna("").to_dict()}

    except Exception as e:
        logger.exception("Error in weekly_orders: %s", e)
        return {"error": "Error processing weekly orders", "details": str(e)}
