import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
SUPPORT_BOT = os.getenv("SUPPORT_BOT", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")

if not ADMIN_ID:
    raise ValueError("ADMIN_ID is not set in environment variables")

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    raise ValueError("ADMIN_ID must be a valid integer")
