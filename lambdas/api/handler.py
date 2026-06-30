import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from routes import checkout, weekly_orders, update_products, products, newsletter

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
    return handler(event, context)
