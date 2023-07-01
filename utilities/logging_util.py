import logging


def init_logger(logger_name: str) -> logging.Logger:
    """
        Create a logger with the given name that logs messages at the console and then return it for future use.
        :param logger_name: string value representing the logger name
        :return: logging.Logger instance
    """

    logger: logging.Logger = logging.getLogger(logger_name)
    logger.setLevel(level=logging.DEBUG)

    formatter: logging.Formatter = logging.Formatter(
        fmt='[%(asctime)s] - [%(levelname)s] * [%(name)s] * [%(module)s -- %(funcName)s -- %(lineno)d] --> %(message)s'
    )

    stream_handler: logging.StreamHandler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)

    logger.addHandler(hdlr=stream_handler)

    return logger
