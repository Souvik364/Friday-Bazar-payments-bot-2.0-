"""
Friday Bazar Payments - Admin Dashboard
========================================
Unified Admin Control Panel
"""

import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

from src.utils.admin_utils import admin_only
from src.services.settings import settings_manager
from src.services.db import db

router = Router()

@router.message(Command("admin", "dashboard"))
@admin_only
async def show_admin_dashboard(message: Message):
    """Show unified admin dashboard"""
    await _send_dashboard(message)

@router.callback_query(F.data == "admin_dashboard")
@admin_only
async def refresh_dashboard(callback: CallbackQuery):
    """Refresh admin dashboard"""
    await callback.answer("🔄 Refreshing...")
    await _send_dashboard(callback.message, is_edit=True)

async def _send_dashboard(message_or_callback, is_edit=False):
    """Helper to render dashboard"""
    
    # helper to safely get user/order counts (could be async)
    # For now, accessing private members of DB is ugly but fast for immediate prototype. 
    # Better to add getter methods in DB.
    # Assuming db._users and db._orders are accessible or we add getters.
    # Let's use what we have or add simple stats getters to DB later.
    # For now, we will try to read if exposed, or just show placeholders if strictly private.
    # Python doesn't enforce private strictly.
    
    # Let's add a safe stats getter to DB in next step if needed, but for now:
    try:
        active_users = len(db._users)
        total_orders = len(db._orders)
        
        # Calculate today's revenue
        today_iso = datetime.now().date().isoformat()
        today_revenue = 0
        today_orders = 0
        
        for order in db._orders:
            if order['created_at'].startswith(today_iso) and order.get('status') in ['approved', 'completed']:
                today_revenue += float(order.get('amount', 0))
                today_orders += 1
                
        pending_approvals = sum(1 for o in db._orders if o.get('status') == 'verification')
        
    except Exception:
        active_users = "N/A"
        total_orders = "N/A"
        today_revenue = 0
        today_orders = 0
        pending_approvals = 0

    # Get system status
    payment_enabled = settings_manager.is_payment_enabled()
    qr_settings = settings_manager.get_qr_settings()
    using_default_qr = qr_settings.get('use_default_qr', False)
    
    status_emoji = "✅ Active" if payment_enabled else "🔴 DISABLED"
    qr_mode = "Static (Default)" if using_default_qr else "Dynamic Generation"
    
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍💼 **ADMIN CONTROL PANEL**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 **SYSTEM STATUS**\n"
        f"• Payment System: {status_emoji}\n"
        f"• QR Mode: {qr_mode}\n"
        f"• Active Users: {active_users}\n"
        f"• Pending Approvals: {pending_approvals}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💰 **REVENUE TODAY**\n"
        f"Total: ₹{today_revenue:,.2f}\n"
        f"Orders: {today_orders}\n"
        f"Avg: ₹{today_revenue/today_orders if today_orders else 0:.0f}/order\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚙️ **QUICK ACTIONS**"
    )
    
    # Keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Review Pending Approvals", callback_data="admin_pending_approvals") 
            if pending_approvals > 0 else 
            InlineKeyboardButton(text="✅ No Pending Approvals", callback_data="noop")
        ],
        [
            InlineKeyboardButton(text="🖼️ QR Settings", callback_data="admin_qr_menu"),
            InlineKeyboardButton(text="🛠️ Manage Services (Prices/QR)", callback_data="admin_price_menu")
        ],
        [
            InlineKeyboardButton(text="🔧 Payment Toggle", callback_data="admin_payment_toggle"),
            InlineKeyboardButton(text="📊 Analytics", callback_data="admin_analytics")
        ],
        [
            InlineKeyboardButton(text="👥 Users", callback_data="admin_users"),
            InlineKeyboardButton(text="💬 Broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_dashboard"),
            InlineKeyboardButton(text="🔙 Exit Admin Mode", callback_data="back_to_main_menu") # Or close
        ]
    ])
    
    if is_edit:
        await message_or_callback.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message_or_callback.answer(text, reply_markup=keyboard, parse_mode="Markdown")
