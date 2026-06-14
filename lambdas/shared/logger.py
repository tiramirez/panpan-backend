import logging

def get_logger(name: str = __name__) -> logging.Logger:
    # Lambda pre-configures the root logger; just set the level.
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
