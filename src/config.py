"""
Friday Bazar Payments - Configuration
======================================
Load environment variables and service catalog
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
    raise ValueError("[ERROR] BOT_TOKEN is not set or still set to placeholder value. Please set it in .env file.")

# Admin Configuration
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
if not ADMIN_IDS:
    print("[WARNING] No ADMIN_IDS configured. Admin features will not work.")

# Payment Configuration
UPI_ID = os.getenv("UPI_ID", "")
UPI_NAME = os.getenv("UPI_NAME", "Friday Bazar")
PAYMENT_TIMEOUT_MINUTES = int(os.getenv("PAYMENT_TIMEOUT_MINUTES", "10"))

if not UPI_ID:
    print("[WARNING] UPI_ID not set. Payment QR generation will fail.")

# Referral Configuration
REFERRAL_COMMISSION_PERCENT = float(os.getenv("REFERRAL_COMMISSION_PERCENT", "10"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "FridayBazarBot")

# Web Server Configuration (for Render)
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBAPP_HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("PORT", "8080"))

# Database paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Google Sheets (optional)
GOOGLE_SHEETS_CREDS_PATH = os.getenv("GOOGLE_SHEETS_CREDS_PATH", "credentials.json")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Friday Bazar Orders")

# Branding
BOT_NAME = "Friday Bazar Payments"
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "FridayBazarSupport")

print("[OK] Configuration loaded successfully")
print(f"[BOT] {BOT_NAME}")
print(f"[ADMINS] {len(ADMIN_IDS)} configured")
print(f"[REFERRAL] Commission: {REFERRAL_COMMISSION_PERCENT}%")
