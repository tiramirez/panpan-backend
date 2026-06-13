import logging
from typing import Any

logger = logging.getLogger(__name__)

def query_with_pagination(table, query_params: dict[str, Any]) -> list[dict[str, Any]]:
    all_items = []
    response = None
    query_count = 0

    try:
        while True:
            query_count += 1
            logger.info(f"Executing query #{query_count}")
            if response and "LastEvaluatedKey" in response:
                query_params["ExclusiveStartKey"] = response["LastEvaluatedKey"]
            response = table.query(**query_params)
            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                raise Exception(f"DynamoDB query failed with status code: {response['ResponseMetadata']['HTTPStatusCode']}")
            items = response.get("Items", [])
            all_items.extend(items)
            logger.info(f"Retrieved {len(items)} items in query #{query_count}")
            if "LastEvaluatedKey" not in response:
                break
        logger.info(f"Query completed. Total items: {len(all_items)} across {query_count} queries")
        return all_items
    except Exception as e:
        logger.exception(f"Error during DynamoDB query: {str(e)}")
        raise
