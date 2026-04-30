import logging
import os

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("auth-service")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

app_handler = logging.FileHandler("logs/app.log")
app_handler.setLevel(logging.INFO)
app_handler.setFormatter(formatter)

error_handler = logging.FileHandler("logs/error.log")
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger.addHandler(app_handler)
logger.addHandler(error_handler)
logger.addHandler(console_handler)