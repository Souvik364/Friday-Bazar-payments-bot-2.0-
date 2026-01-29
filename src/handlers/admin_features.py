"""
Friday Bazar Payments - Admin Consolidated Features
====================================================
Handles Pending Approvals, Analytics, Users, and Broadcast logic.
"""

import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

from src.utils.admin_utils import admin_only, log_admin_action
from src.services.db import db

router = Router()

class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    confirm_broadcast = State()

# =========================================================
#                   PENDING APPROVALS
# =========================================================
@router.callback_query(F.data == "admin_pending_approvals")
@admin_only
async def show_pending_approvals(callback: CallbackQuery):
    """Show list of orders waiting for approval"""
    # Filter orders
    pending = [o for o in db._orders if o.get('status') == 'verification']
    
    if not pending:
        await callback.answer("✅ No pending approvals!", show_alert=True)
        return

    text = f"⏳ **Pending Approvals ({len(pending)})**\n\nSelect an order to verify:"
    
    keyboard = []
    
    # Show oldest first? Or newest? Usually oldest first to clear backlog.
    # Let's show newest at top.
    for order in reversed(pending):
        oid = order['order_id']
        amt = order['amount']
        svc = order['service_name']
        user_id = order['user_id']
        
        btn_text = f"🆔 {oid} | ₹{amt} | {svc}"
        keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"admin_verify_order:{oid}")])
        
    keyboard.append([InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_dashboard")])
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data.startswith("admin_verify_order:"))
@admin_only
async def verify_specific_order(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    order = await db.get_order(order_id)
    
    if not order or order['status'] != 'verification':
        await callback.answer("Order not found or already processed.", show_alert=True)
        await show_pending_approvals(callback)
        return
        
    # Show details
    text = (
        f"🔎 **Verifying Order #{order_id}**\n\n"
        f"👤 User ID: `{order['user_id']}`\n"
        f"🛍️ Service: {order['service_name']} ({order['plan_duration']})\n"
        f"💰 Amount: **₹{order['amount']}**\n"
        f"🕒 Time: {order['created_at']}\n"
    )
    
    # We can't easily "show" the photo here without resending the message or asking DB for file_id if we stored it?
    # Usually payment handler forwards photo to admin channel. 
    # If we want to show it here, we need file_id. 
    # Current DB schema in payment.py doesn't seem to explicitly save 'screenshot_file_id' to order object?
    # WAIT, payment.py sends photo to ADMIN_ID. 
    # If we want to view it here, we'd need to have stored it. 
    # Let's assume admins check their PMs for the photo, this is just for action.
    
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_approve:{order_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_reject:{order_id}")
        ],
        [InlineKeyboardButton(text="🔙 Back to Pending List", callback_data="admin_pending_approvals")]
    ]
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")


# =========================================================
#                       ANALYTICS
# =========================================================
@router.callback_query(F.data == "admin_analytics")
@admin_only
async def show_analytics(callback: CallbackQuery):
    """Show detailed analytics"""
    
    # Calculate stats
    total_revenue = 0
    total_orders = 0
    today_revenue = 0
    month_revenue = 0
    
    now = datetime.now()
    today_str = now.date().isoformat()
    month_str = now.strftime("%Y-%m")
    
    # Services breakdown
    service_sales = {}
    
    for order in db._orders:
        if order.get('status') in ['approved', 'completed', 'fulfillment']:
            amt = float(order.get('amount', 0))
            total_revenue += amt
            total_orders += 1
            
            created = order.get('created_at', '')
            if created.startswith(today_str):
                today_revenue += amt
            if created.startswith(month_str):
                month_revenue += amt
                
            svc = order.get('service_name', 'Unknown')
            service_sales[svc] = service_sales.get(svc, 0) + 1

    # Top service
    top_service = max(service_sales.items(), key=lambda x: x[1])[0] if service_sales else "N/A"
    
    text = (
        "📊 **Analytics Dashboard**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💰 **Revenue**\n"
        f"• Today: ₹{today_revenue:,.2f}\n"
        f"• This Month: ₹{month_revenue:,.2f}\n"
        f"• All Time: ₹{total_revenue:,.2f}\n\n"
        "📦 **Orders**\n"
        f"• Total Completed: {total_orders}\n"
        f"• Top Service: {top_service}\n\n"
        "👥 **User Base**\n"
        f"• Total Users: {len(db._users)}\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    keyboard = [[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_dashboard")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")


# =========================================================
#                       USERS
# =========================================================
@router.callback_query(F.data == "admin_users")
@admin_only
async def show_users(callback: CallbackQuery):
    """Show user stats"""
    total_users = len(db._users)
    
    # New today
    today_str = datetime.now().date().isoformat()
    new_users = sum(1 for u in db._users.values() if u.get('joined_at', '').startswith(today_str))
    
    text = (
        "👥 **User Management**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"• Total Users: **{total_users}**\n"
        f"• New Today: **{new_users}**\n\n"
        "_(User search features coming soon)_"
    )
    
    keyboard = [[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_dashboard")]]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")


# =========================================================
#                       BROADCAST
# =========================================================
@router.callback_query(F.data == "admin_broadcast")
@admin_only
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    """Start broadcast flow"""
    await state.set_state(BroadcastStates.waiting_for_message)
    
    text = (
        "📢 **Broadcast Message**\n\n"
        "Send the message you want to broadcast to **ALL** users.\n"
        "Supported formats: Text, Photo, Video.\n\n"
        "Type `cancel` to abort."
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")

@router.message(BroadcastStates.waiting_for_message)
@admin_only
async def receive_broadcast_message(message: Message, state: FSMContext):
    if message.text and message.text.lower() == "cancel":
        await state.clear()
        await message.answer("❌ Broadcast cancelled.")
        return # Need to show dashboard again manually or they use /admin

    # Copy message to confirm
    await message.copy_to(chat_id=message.chat.id)
    
    await state.update_data(message_id=message.message_id, chat_id=message.chat.id)
    await state.set_state(BroadcastStates.confirm_broadcast)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Send to All Users", callback_data="broadcast_confirm")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="broadcast_cancel")]
    ])
    
    await message.answer(
        "👆 **Preview above.**\n\n"
        f"Are you sure you want to send this to **{len(db._users)}** users?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "broadcast_confirm")
@admin_only
async def execute_broadcast(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get('message_id')
    from_chat = data.get('chat_id')
    
    await callback.message.edit_text("⏳ **Sending Broadcast...**\nThis may take a while.")
    
    count = 0
    blocked = 0
    
    for user_id_str in db._users:
        try:
            user_id = int(user_id_str)
            await callback.bot.copy_message(
                chat_id=user_id,
                from_chat_id=from_chat,
                message_id=msg_id
            )
            count += 1
            await asyncio.sleep(0.05) # Rate limit protection
        except Exception:
            blocked += 1
    
    await callback.message.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"Sent: {count}\n"
        f"Failed/Blocked: {blocked}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_dashboard")]])
    )
    await state.clear()
    await log_admin_action(callback.from_user.id, "Admin", "broadcast", {"sent": count, "blocked": blocked})

@router.callback_query(F.data == "broadcast_cancel")
@admin_only
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast cancelled.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_dashboard")]]))
