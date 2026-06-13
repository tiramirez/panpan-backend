import logging

def get_logger():
    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    return logger
