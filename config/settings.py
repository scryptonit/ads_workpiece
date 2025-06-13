import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

# Загрузка переменных окружения из .env
load_dotenv()

# -------------------------
# Основные настройки проекта
# -------------------------

ADSPOWER_API_URL = os.getenv("ADSPOWER_API_URL", "http://localhost:50325")
ENCRYPTED_WALLETS_PATH = os.getenv("ENCRYPTED_WALLETS_PATH")
WALLET_SOURCE = os.getenv("WALLET_SOURCE", "keychain").strip().lower()
WALLET_KEY_PATH = os.getenv("WALLET_KEY_PATH")

# -------------------------
# Логирование через loguru
# -------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logger.remove()

logger.add(
    sys.stdout,
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

os.makedirs("logs", exist_ok=True)
log_file = f"logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

logger.add(
    log_file,
    level=LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {module}:{function}:{line} - {message}",
    rotation="10 MB",
    retention="7 days",
    compression="zip"
)

logger.debug("Settings loaded successfully.")
