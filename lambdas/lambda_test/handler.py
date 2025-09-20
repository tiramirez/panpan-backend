import time
from utils import logger

logger = logger.get_logger()

def lambda_handler(event, context):
    logger.info("Program starting...")
    time.sleep(10)  # Pause execution for 4 seconds
    logger.info("Program continuing after 4-second delay.")
    
    return {"statusCode": 200, "body": "Hello"}