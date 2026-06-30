import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from routes import checkout, weekly_orders, update_products, products, newsletter

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="panpan-api")
logger.info("panpan-api initializing")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(checkout.router)
app.include_router(weekly_orders.router)
app.include_router(update_products.router)
app.include_router(newsletter.router)

handler = Mangum(app, lifespan="off")


def lambda_handler(event, context):
    method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "UNKNOWN")
    path = event.get("path") or event.get("rawPath", "UNKNOWN")
    logger.info("Request: %s %s", method, path)
    return handler(event, context)
