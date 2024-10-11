import logging


def get_client_logger(logger_name: str = "application_logger"):
    # Configure logging before we do anything else.
    # Application logs need a place to live.
    client_logger = logging.getLogger(logger_name)
    client_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    client_logger.addHandler(ch)

    return client_logger
