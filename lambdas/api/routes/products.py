import datetime
import json
import os
from typing import Optional

from boto3 import client, resource
from fastapi import APIRouter, Query

from shared.s3 import read_json
from shared.logger import get_logger, log_event

router = APIRouter()
logger = get_logger(__name__)


@router.get("/products")
def get_products(did: str = Query(default=None)):
    try:
        bucket = os.environ["PANPAN_BUCKET_NAME"]
        s3 = client("s3")

        experiment = _get_active_experiment()
        variant = None
        if experiment and did:
            try:
                variant = _assign_variant(did, experiment)
            except Exception as e:
                logger.warning("Variant assignment failed, using fallback: %s", e)

        if variant and experiment:
            s3_key = f"experiments/products_list_{experiment['id']}_{variant}.json"
        else:
            s3_key = "products_list.json"

        data = read_json(s3, bucket, s3_key)

        product_count = len(data.get("Items", []))
        logger.info("Fetched %d products (variant=%s)", len(data.get("Items", [])), variant)
        log_event(logger, "menu_queried", product_count=product_count)

        if did and variant:
            _track_impression(did, variant, experiment)

        response = {"ok": True, "data": data}
        if experiment:
            response["experiment"] = {
                "id": experiment["id"],
                "variant": variant,
                "expires_at": experiment["expires_at"],
            }
        return response

    except Exception as e:
        logger.exception("Error fetching products: %s", e)
        return {"ok": False, "error": str(e)}


def _get_active_experiment():
    raw = os.environ.get("PANPAN_ACTIVE_EXPERIMENTS", "[]")
    experiments = json.loads(raw)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for exp in experiments:
        if exp.get("expires_at", "") > now:
            return exp
    return None


def _assign_variant(device_id: str, experiment: dict) -> str:
    table = resource("dynamodb").Table(os.environ["PANPAN_TABLE_NAME"])
    exp_id = experiment["id"]

    item = table.get_item(
        Key={"PK": f"exp#{exp_id}", "SK": f"dev#{device_id}"}
    ).get("Item")

    if item:
        return item["variant"]

    variants = experiment.get("variants", ["a", "b"])
    seed = device_id + exp_id
    hash_val = 2166136261
    for ch in seed:
        hash_val ^= ord(ch)
        hash_val = (hash_val * 16777619) & 0xFFFFFFFF
    variant = variants[hash_val % len(variants)]

    try:
        table.put_item(Item={
            "PK": f"exp#{exp_id}",
            "SK": f"dev#{device_id}",
            "variant": variant,
            "expires_at": experiment["expires_at"],
            "assigned_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.warning("Failed to persist variant assignment: %s", e)

    return variant


def _track_impression(device_id: str, variant: str, experiment: Optional[dict]):
    try:
        week_str = datetime.datetime.now().strftime("%G-%V")
        table = resource("dynamodb").Table(os.environ["PANPAN_TABLE_NAME"])
        item = {
            "PK": week_str,
            "SK": f"ev#{device_id}",
            "variant": variant,
        }
        if experiment:
            item["experiment_id"] = experiment["id"]
        table.put_item(Item=item)
        log_event(logger, "device_registered", device_id=device_id) 
        
    except Exception as e:
        logger.warning("Impression tracking failed: %s", e)
