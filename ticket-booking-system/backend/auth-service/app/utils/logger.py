import logging
import os


os.makedirs("logs", exist_ok=True)


class MaxLevelFilter(logging.Filter):
    def __init__(self, max_level: int):
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord):
        return record.levelno <= self.max_level


logger = logging.getLogger("auth-service")
logger.setLevel(logging.INFO)


formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


if not logger.handlers:

    app_handler = logging.FileHandler(
        "logs/app.log",
        encoding="utf-8",
    )

    app_handler.setLevel(logging.INFO)

    app_handler.addFilter(
        MaxLevelFilter(logging.WARNING)
    )

    app_handler.setFormatter(formatter)


    error_handler = logging.FileHandler(
        "logs/error.log",
        encoding="utf-8",
    )

    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)


    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)


    logger.addHandler(app_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)


logger.propagate = False