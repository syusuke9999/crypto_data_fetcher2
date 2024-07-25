import logging


def create_null_logger():
    logger = logging.getLogger("null")
    logger.setLevel(logging.DEBUG)
    handler = logging.NullHandler()
    logger.addHandler(handler)
    return logger
