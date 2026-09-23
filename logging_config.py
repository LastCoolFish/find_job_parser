import logging
from logging.handlers import RotatingFileHandler


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger configured to write to logs/<name>.log, creating it on first call.
    Calling this again with the same name returns the same logger without adding a duplicate handler.

    :param name: logger name, conventionally __name__ of the calling module
    :return: configured logging.Logger
    """

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)



    handler = RotatingFileHandler(
        f"logs/{name}.log",
        maxBytes=5 * 1024 * 1024,  # 5 МБ
        backupCount=5,
        encoding="utf-8",
    )
    formatter = logging.Formatter("%(asctime)s | %(name)s %(funcName)s %(lineno)d | %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
