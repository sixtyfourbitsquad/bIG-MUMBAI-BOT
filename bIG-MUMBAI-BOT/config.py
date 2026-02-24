import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")

ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")
ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS if admin_id.strip()]

if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS not found in .env file. At least one admin ID is required.")

DATABASE_PATH = "bot_database.db"
DEFAULT_INTERVAL_HOURS = 8
DEFAULT_AUTO_MESSAGES_ENABLED = True

