"""
Friday Bazar Payments - Admin Handler
======================================
Handles admin approval logic and commission distribution
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from src.services.db import db
from src.services.sheets import sheets_logger
from src.config import ADMIN_IDS, REFERRAL_COMMISSION_PERCENT
from src.utils.helpers import format_currency, calculate_commission

router = Router()

# FSM States for collecting user details
class FulfillmentStates(StatesGroup):
    waiting_for_details = State()

# Store order context for fulfillment
fulfillment_context = {}

@router.callback_query(F.data.startswith("admin_approve:"))
async def admin_approve(callback: CallbackQuery, state: FSMContext):
    """Admin approves payment - triggers fulfillment flow"""
    # INSTANT FEEDBACK
    await callback.answer("✅ Approving...")
    
    # Check if user is admin
    if callback.from_user.id not in ADMIN_IDS:
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n❌ Unauthorized",
            parse_mode="Markdown"
        )
        return
    
    order_id = callback.data.split(":")[1]
    order = await db.get_order(order_id)
    
    if not order:
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n❌ Order not found",
            parse_mode="Markdown"
        )
        return
    
    if order['status'] != 'verification':
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\nℹ️ Order already processed",
            parse_mode="Markdown"
        )
        return
    
    # Update order status
    await db.update_order(order_id, {"status": "approved"})
    
    # Update admin message
    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n✅ **APPROVED** by @{callback.from_user.username}",
        parse_mode="Markdown"
    )
    
    # Request user details from customer
    user_id = order['user_id']
    
    # Store context for later
    fulfillment_context[user_id] = order_id
    
    from src.config import SUPPORT_USERNAME
    
    details_text = (
        f"✅ *Payment Approved!*\n\n"
        f"🎉 Your payment has been verified.\n\n"
        f"*Order Details:*\n"
        f"🆔 Order ID: `{order_id}`\n"
        f" Service: {order['service_name']}\n"
        f"⏱️ Plan: {order['plan_duration']}\n"
        f"💰 Amount Paid: ₹{format_currency(order['amount'])}\n\n"
        f"📢 *Next Step - Activation:*\n"
        f"👉 Contact: @{SUPPORT_USERNAME}\n\n"
        f"*Please mention:*\n"
        f"• Your Order ID: `{order_id}`\n"
        f"• Service: {order['service_name']}\n"
        f"• Your Gmail (for YouTube Premium)\n\n"
        f"Our team will activate your subscription within 24 hours!"
    )
    
    await callback.message.bot.send_message(
        chat_id=user_id,
        text=details_text,
        parse_mode="Markdown"
    )
    
    # Set state for this user
    await state.set_state(FulfillmentStates.waiting_for_details)
    await state.update_data(order_id=order_id)
    
    # Process referral commission in background
    asyncio.create_task(process_referral_commission(order))

@router.message(FulfillmentStates.waiting_for_details)
async def receive_user_details(message: Message, state: FSMContext):
    """Receive user details for fulfillment"""
    import re
    from src.services.subscription import subscription_service
    from datetime import datetime
    
    data = await state.get_data()
    order_id = data.get("order_id")
    
    if not order_id:
        await state.clear()
        return
    
    user_details = message.text
    
    # Extract and validate email from user details
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_matches = re.findall(email_pattern, user_details)
    
    user_email = None
    if email_matches:
        user_email = email_matches[0]  # Use first email found
        
        # Store email in user profile
        await db.update_user(message.from_user.id, {"email": user_email})
    
    # Get order details
    order = await db.get_order(order_id)
    
    # Activate subscription
    await subscription_service.activate_subscription(
        user_id=message.from_user.id,
        service_name=order['service_name'],
        plan_duration=order['plan_duration']
    )
    
    # Update order with user details
    await db.update_order(order_id, {
        "user_details": user_details,
        "user_email": user_email,
        "status": "fulfillment",
        "activated_at": datetime.now().isoformat()
    })
    
    # Add purchase to user history
    await db.add_purchase_to_user(message.from_user.id, order_id, order['amount'])
    
    # Get updated order data for Sheets
    updated_order = await db.get_order(order_id)
    user = await db.get_user(message.from_user.id)
    
    # Enhance order data for Google Sheets logging
    updated_order['user_email'] = user_email or ''
    updated_order['subscription_expiry'] = user.get('subscription_expiry', '')
    
    # Log to Google Sheets with enhanced data
    await sheets_logger.log_order(updated_order)
    
    # Get subscription info for user notification
    sub_info = await subscription_service.get_subscription_info(message.from_user.id)
    expiry_date_str = ""
    if sub_info['expiry_date']:
        expiry_date_str = f"\n📅 Expires: {sub_info['expiry_date'].strftime('%d %b %Y')}"
    
    # Notify user
    await message.answer(
        f"✅ **Details Received!**\n\n"
        f"🎉 Your **{order['service_name']}** subscription is now active!\n\n"
        f"⏱️ Plan: {order['plan_duration']}{expiry_date_str}\n"
        f"📧 Email: {user_email or 'N/A'}\n"
        f"🆔 Order ID: `{order_id}`\n\n"
        f"📧 You'll receive activation details within 24 hours.\n\n"
        f"✨ Thank you for choosing Friday Bazar!",
        parse_mode="Markdown"
    )
    
    # Notify admin
    admin_text = (
        f"📋 **User Details Received**\n\n"
        f"🆔 Order ID: `{order_id}`\n"
        f"👤 User: {message.from_user.first_name} (@{message.from_user.username or 'N/A'})\n"
        f"🛍️ Service: {order['service_name']} ({order['plan_duration']})\n"
        f"📧 Email: {user_email or 'N/A'}\n\n"
        f"📝 **Full Details:**\n{user_details}\n\n"
        f"✅ Subscription activated\n"
        f"⚠️ Please proceed with account activation."
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                parse_mode="Markdown"
            )
        except:
            pass
    
    await state.clear()

@router.callback_query(F.data.startswith("admin_reject:"))
async def admin_reject(callback: CallbackQuery):
    """Admin rejects payment"""
    
    # Check if user is admin
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Unauthorized", show_alert=True)
        return
    
    order_id = callback.data.split(":")[1]
    order = await db.get_order(order_id)
    
    if not order:
        await callback.answer("❌ Order not found", show_alert=True)
        return
    
    # Update order status
    await db.update_order(order_id, {"status": "rejected"})
    
    # Notify admin
    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n❌ **REJECTED** by @{callback.from_user.username}",
        parse_mode="Markdown"
    )
    await callback.answer("Payment rejected")
    
    # Notify user
    user_id = order['user_id']
    await callback.message.bot.send_message(
        chat_id=user_id,
        text=(
            f"❌ **Payment Verification Failed**\n\n"
            f"Unfortunately, we couldn't verify your payment for order `{order_id}`.\n\n"
            f"Possible reasons:\n"
            f"• Incorrect amount paid\n"
            f"• Screenshot unclear\n"
            f"• Payment not received\n\n"
            f"Please contact support if you believe this is an error."
        ),
        parse_mode="Markdown"
    )

async def process_referral_commission(order: dict):
    """Process referral commission when order is approved"""
    user_id = order['user_id']
    amount = order['amount']
    
    # Get user and check if they were referred
    user = await db.get_user(user_id)
    referrer_id = user.get('referred_by')
    
    if referrer_id:
        # Calculate commission
        commission = calculate_commission(amount, REFERRAL_COMMISSION_PERCENT)
        
        # Add coins to referrer
        await db.add_coins(referrer_id, commission, f"Referral from user {user_id}")
        
        # Increment referral count
        await db.increment_referral_count(referrer_id)
        
        # Update order with commission info
        await db.update_order(order['order_id'], {
            "referrer_id": referrer_id,
            "commission_paid": commission
        })
        
        # Notify referrer
        from main import bot
        try:
            await bot.send_message(
                chat_id=referrer_id,
                text=(
                    f"🎉 **Commission Earned!**\n\n"
                    f"Your referral just completed a purchase!\n\n"
                    f"💰 Commission: **{format_currency(commission)}**\n"
                    f"📦 Order: {order['service_name']}\n"
                    f"💵 Order Amount: {format_currency(amount)}\n\n"
                    f"✨ Total Coins: {format_currency((await db.get_user(referrer_id))['coins'])}"
                ),
                parse_mode="Markdown"
            )
        except:
            pass

@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Show admin commands (admin only)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ You are not authorized to use admin commands.")
        return
    
    admin_text = (
        f"👨‍💼 **Admin Panel**\n\n"
        f"🔔 You will automatically receive:\n"
        f"• Payment verification requests\n"
        f"• User details for fulfillment\n\n"
        f"✅ Approve payments by clicking buttons\n"
        f"❌ Reject invalid payments\n\n"
        f"All orders are logged to Google Sheets automatically."
    )
    
    await message.answer(admin_text, parse_mode="Markdown")
