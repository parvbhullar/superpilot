import logging

LOG_LEVEL = logging.DEBUG

def get_logger(logger_name: str = "application_logger"):
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


def get_log_level_from_str(log_level_str: str = LOG_LEVEL) -> int:
    log_level_dict = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }

    return log_level_dict.get(log_level_str.upper(), logging.INFO)


def setup_logger(
    name: str = __name__,
    log_level: int = get_log_level_from_str("INFO"),
    logfile_name: str | None = None,
) -> logging.LoggerAdapter:
    logger = logging.getLogger(name)

    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s %(filename)20s%(lineno)4s : %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
    )

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    if logfile_name:
        is_containerized = os.path.exists("/.dockerenv")
        file_name_template = (
            "/var/log/{name}.log" if is_containerized else "./log/{name}.log"
        )
        file_handler = logging.FileHandler(file_name_template.format(name=logfile_name))
        logger.addHandler(file_handler)

    return logger