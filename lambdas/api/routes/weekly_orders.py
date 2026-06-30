import json
import os

import boto3
import pandas as pd
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

        orders_items = query_with_pagination(table, {
            "IndexName": "GSI1",
            "KeyConditionExpression": "#index = :pk",
            "ExpressionAttributeNames": {"#index": "GSI1-PK"},
            "ExpressionAttributeValues": {":pk": str(week)},
        })
        orders = pd.DataFrame(orders_items)

        summary_items = query_with_pagination(table, {
            "IndexName": "GSI2",
            "KeyConditionExpression": "#index = :pk",
            "ExpressionAttributeNames": {"#index": "GSI2-PK"},
            "ExpressionAttributeValues": {":pk": str(week)},
        })
        summary = pd.DataFrame(summary_items)

        df = (
            orders
            .pivot_table(
                index=["PK", "email", "firstName", "lastName", "phone"],
                columns="product_name",
                aggfunc={"product_quantity": "sum"},
            )
            .product_quantity
            .reset_index()
            .fillna("")
        )

        for col in ["created_at", "donation", "comments", "menu_version"]:
            df[col] = df.astype({"PK": str}).PK.map(
                summary.astype({"PK": str}).set_index("PK")[col].to_dict()
            )

        df["email"] = df.email.str.replace("u#", "")
        df["firstName"] = df.firstName.str.replace("u#", "")
        df["lastName"] = df.lastName.str.replace("u#", "")
        df["phone"] = df.phone.str.replace("u#", "")

        new_columns = ["created_at", "menu_version", "email", "firstName", "lastName", "phone", "comments", "donation"] + list(products.name.sort_values().unique())
        if "tip" in summary.columns:
            df["tip"] = df.astype({"PK": str}).PK.map(
                summary.astype({"PK": str}).set_index("PK").tip.to_dict()
            ).astype(float).round(2)
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
