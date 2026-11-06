import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://example.com")
APP_SECRET = os.getenv("APP_SECRET", "")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/demo_platform.db")
PORT = int(os.getenv("PORT", "8000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN .env faylida sozlanmagan")

if len(APP_SECRET) < 24:
    raise RuntimeError("APP_SECRET kamida 24 belgidan iborat bo‘lsin")
