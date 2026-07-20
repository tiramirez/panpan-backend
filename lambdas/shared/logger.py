import json
import logging
import time


def get_logger(name: str = __name__) -> logging.Logger:
    # Lambda pre-configures the root logger; just set the level.
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def log_event(logger: logging.Logger, event_name: str, **kwargs) -> None:
    logger.info(json.dumps({"event": event_name, "ts": int(time.time()), **kwargs}))
