# ============================================================
#  app/config.py — все настройки из .env
# ============================================================
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_IDS = [int(x) for x in os.getenv("OWNER_IDS", "").split(",") if x.strip().isdigit()]
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://bot:botpass@localhost:5432/anonbot")
REDIS_URL = os.getenv("REDIS_URL", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", 8080))
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "ru")
PAGE_SIZE = 5


def is_owner(uid: int) -> bool:
    return uid in OWNER_IDS