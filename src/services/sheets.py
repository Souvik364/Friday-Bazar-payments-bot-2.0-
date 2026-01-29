"""
Friday Bazar Payments - Google Sheets Integration
=================================================
Logs orders to Google Sheets for record keeping
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from typing import Dict
import os
import json

class SheetsLogger:
    def __init__(self):
        self.enabled = False
        self.sheet = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Google Sheets connection"""
        try:
            # Check if credentials exist
            creds_path = os.getenv("GOOGLE_SHEETS_CREDS_PATH", "credentials.json")
            if not os.path.exists(creds_path):
                print("[WARNING] Google Sheets credentials not found. Logging disabled.")
                return
            
            # Setup credentials
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            client = gspread.authorize(creds)
            
            # Open the sheet
            sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Friday Bazar Orders")
            self.sheet = client.open(sheet_name).sheet1
            
            # Create headers if sheet is empty
            if not self.sheet.row_values(1):
                self.sheet.append_row([
                    "Order ID", "Date", "User ID", "Username", "Email",
                    "Service", "Plan", "Amount", "Status", "Subscription Expiry",
                    "Referrer ID", "Commission Paid"
                ])
            
            self.enabled = True
            print("[OK] Google Sheets logging enabled")
            
        except Exception as e:
            print(f"[WARNING] Google Sheets error: {e}")
            self.enabled = False
    
    async def log_order(self, order_data: dict):
        """Log order to Google Sheets"""
        if not self.enabled:
            return
        
        try:
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            # Prepare row data
            row = [
                order_data.get("order_id", ""),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                order_data.get("user_id", ""),
                order_data.get("username", ""),
                order_data.get("user_email", ""),  # Email column
                order_data.get("service_name", ""),
                order_data.get("plan_duration", ""),
                order_data.get("amount", 0),
                order_data.get("status", "pending"),
                order_data.get("subscription_expiry", ""),  # Expiry column
                order_data.get("referrer_id", "N/A"),
                order_data.get("commission_paid", 0)
            ]
            
            # Run sheet.append_row in executor (sync operation)
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(
                    executor,
                    self.sheet.append_row,
                    row
                )
            
            print(f"[SHEETS] Logged order {order_data.get('order_id')} to Google Sheets")
            
        except Exception as e:
            print(f"[WARNING] Failed to log to Google Sheets: {e}")

# Global sheets logger instance
sheets_logger = SheetsLogger()
