import os
from fastapi import FastAPI
from mangum import Mangum
from routes import checkout, weekly_orders, update_products, products

app = FastAPI(title="panpan-api")

app.include_router(products.router)
app.include_router(checkout.router)
app.include_router(weekly_orders.router)
app.include_router(update_products.router)

handler = Mangum(app, lifespan="off")


def lambda_handler(event, context):
    return handler(event, context)
