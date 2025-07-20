import time
from utils import logger

logger = logger.get_logger()

def lambda_handler(event, context):
    logger.info("Program starting...")
    time.sleep(4)  # Pause execution for 5 seconds
    logger.info("Program continuing after 5-second delay.")
    
    return {"statusCode": 200, "body": "Hello"}