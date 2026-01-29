"""
Friday Bazar Payments - Payment Handler
========================================
Handles QR generation, timers, payment verification, and screenshot uploads
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

from src.keyboards.menus import get_payment_verification_buttons, get_admin_approval_buttons
from src.data.services import get_service
from src.utils.helpers import generate_upi_qr, format_currency, get_expiry_time
from src.services.db import db
from src.config import UPI_ID, UPI_NAME, PAYMENT_TIMEOUT_MINUTES, ADMIN_IDS

router = Router()

# FSM States
class PaymentStates(StatesGroup):
    waiting_for_screenshot = State()

# Store active payment timers
active_timers = {}

@router.callback_query(F.data.startswith("buy:"))
async def initiate_payment(callback: CallbackQuery, state: FSMContext):
    """
    Handle purchase button click
    Format: buy:service_id:duration:price
    Optimized with instant callback response
    """
    # INSTANT FEEDBACK - Answer callback immediately
    await callback.answer("⏳ Processing...")
    
    from src.services.settings import settings_manager
    
    # Check if payment system enabled
    if not settings_manager.is_payment_enabled():
        msg = settings_manager.get_disabled_message()
        await callback.message.edit_text(
            f"🚫 **Service Temporarily Unavailable**\n\n{msg}",
            reply_markup=None, # Or back button
            parse_mode="Markdown"
        )
        return

    from src.data.services import is_service_available, get_service
    from src.config import SUPPORT_USERNAME
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    parts = callback.data.split(":")
    service_id = parts[1]
    plan_duration = parts[2]
    price = float(parts[3])
    
    service = get_service(service_id)

    if not service:
        await callback.message.edit_text("❌ Service not found. Please try again.")
        return
    
    # Check if service is demo/unavailable
    if not is_service_available(service_id):
        # Demo service - redirect to support
        demo_purchase_text = (
            f"{service['emoji']} *{service['name']}*\n\n"
            f"📦 Plan: *{plan_duration}*\n"
            f"💰 Price: *₹{price}*\n\n"
            "📢 *This service is available on request!*\n\n"
            "💬 To purchase this service:\n"
            f"👉 Contact: @{SUPPORT_USERNAME}\n\n"
            "*What to mention:*\n"
            f"• Service: {service['name']}\n"
            f"• Plan: {plan_duration}\n"
            f"• Your requirements\n\n"
            "Our team will assist you with:\n"
            "✅ Service activation\n"
            "✅ Payment details\n"
            "✅ Custom configurations"
        )
        
        await callback.message.edit_text(
            demo_purchase_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back to Services", callback_data="back_to_services")]
            ]),
            parse_mode="Markdown"
        )
        return
    
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    
    # Check if this is first YouTube Premium purchase (show free month info)
    if service_id == "youtube":
        user_purchases = user.get('purchases', [])
        has_bought_youtube = any(p.get('service_id') == 'youtube' for p in user_purchases)
        
        if not has_bought_youtube:
            # First time YouTube user - Show free month offer with support contact
            free_msg = (
                "🎁 *SPECIAL OFFER FOR NEW USERS!*\n\n"
                "✨ Get *1 MONTH FREE* YouTube Premium!\n\n"
                "📢 *To claim your free month:*\n"
                f"👉 Contact: @{SUPPORT_USERNAME}\n\n"
                "*Mention:*\n"
                "• You're a new user\n"
                "• Your User ID: `{user_id}`\n"
                "• Request: Free YouTube Premium\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "*Or purchase now:*\n"
                "💰 Continue to pay ₹25 for 1 month →"
            )
            
            await callback.message.edit_text(
                free_msg.format(user_id=user_id),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💰 Pay ₹25 Now", callback_data=f"buy_direct:{service_id}:{plan_duration}:{price}")],
                    [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_services")]
                ]),
                parse_mode="Markdown"
            )
            return
    
    # Regular payment flow for YouTube (₹25) and any available service
    await _create_payment_order(callback, service_id, service, plan_duration, price)



@router.callback_query(F.data.startswith("buy_direct:"))
async def initiate_direct_payment(callback: CallbackQuery, state: FSMContext):
    """
    Handle direct purchase (bypass all checks)
    Format: buy_direct:service_id:duration:price
    """
    parts = callback.data.split(":")
    service_id = parts[1]
    plan_duration = parts[2]
    price = float(parts[3])
    
    service = get_service(service_id)
    if not service:
        await callback.answer("❌ Service not found", show_alert=True)
        return
    
    # Direct payment - no checks, just create order
    await _create_payment_order(callback, service_id, service, plan_duration, price)
    await callback.answer("✅ Payment QR generated!")

async def _create_payment_order(callback, service_id, service, plan_duration, price):
    """Helper to create payment order with async QR generation (optimized)"""
    from src.utils.helpers import generate_upi_qr_async
    
    # Show loading message immediately
    loading_msg = await callback.message.edit_text(
        f"⏳ **Preparing payment for {service['name']}...**\n\n"
        "Creating your order and generating QR code...",
        parse_mode="Markdown"
    )
    
    # Create order data
    order_data = {
        "user_id": callback.from_user.id,
        "username": callback.from_user.username or callback.from_user.first_name,
        "service_id": service_id,
        "service_name": service['name'],
        "plan_duration": plan_duration,
        "amount": price,
        "payment_screenshot": None,
        "user_details": None
    }
    
    # Start order creation and QR generation concurrently
    order_task = db.create_order(order_data)
    
    # QR Logic
    from src.services.settings import settings_manager
    qr_settings = settings_manager.get_qr_settings()
    
    # Resolve UPI Config
    upi_id = qr_settings.get("upi_id") or UPI_ID
    upi_name = qr_settings.get("upi_name") or UPI_NAME

    # Check if Plan has custom QR
    selected_plan = next((p for p in service['plans'] if p['duration'] == plan_duration), None)
    
    if selected_plan and selected_plan.get("custom_qr_file_id"):
        # Use Plan Specific QR
        order_id = await order_task
        qr_image = selected_plan["custom_qr_file_id"]
    elif qr_settings.get("use_default_qr") and qr_settings.get("default_qr_file_id"):
        # Use Default QR
        order_id = await order_task
        qr_image = qr_settings["default_qr_file_id"] 
    else:
        # Dynamic QR
        qr_task = generate_upi_qr_async(upi_id, upi_name, price, "TEMP")
        
        # Wait for both
        order_id, qr_temp = await asyncio.gather(order_task, qr_task)
        
        # Regenerate QR
        qr_image = await generate_upi_qr_async(upi_id, upi_name, price, order_id)
    
    # Payment instruction message
    expiry_time = get_expiry_time(PAYMENT_TIMEOUT_MINUTES)
    payment_text = (
        "━━━━━━━━━━━━━━━━━\n"
        "💳 **Payment Details**\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        f"🔹 **Service:** {service['name']}\n"
        f"⏱️ **Plan:** {plan_duration}\n"
        f"💰 **Amount:** {format_currency(price)}\n\n"
        f"🆔 **Order ID:** `{order_id}`\n"
        f"⏰ **Expires:** {expiry_time}\n\n"
        f"📸 **Action Required:**\n"
        f"1. Scan QR / Pay to `{upi_id}`\n"
        f"2. Upload Screenshot below\n"
    )
    
    # Delete loading message
    await loading_msg.delete()
    
    # Send QR code with instructions
    await callback.message.answer_photo(
        photo=qr_image,
        caption=payment_text,
        reply_markup=get_payment_verification_buttons(order_id),
        parse_mode="Markdown"
    )
    
    # Start payment timer in background
    asyncio.create_task(start_payment_timer(order_id, callback.from_user.id, callback.message.chat.id))

async def start_payment_timer(order_id: str, user_id: int, chat_id: int):
    """
    Payment timer with countdown warnings (optimized)
    Sends warnings at 5 min, 3 min, 1 min remaining
    """
    # Import bot instance
    from main import bot
    
    timeout_seconds = PAYMENT_TIMEOUT_MINUTES * 60
    
    # Warning intervals (seconds before expiry, message)
    warnings = [
        (300, "⏰ **5 minutes remaining!**\n\nPlease complete your payment soon."),
        (180, "⚠️ **3 minutes left!**\n\nHurry up! Complete your payment to avoid order cancellation."),
        (60, "🚨 **FINAL REMINDER: 1 minute left!**\n\n⏱️ Your order will expire soon!")
    ]
    
    # Send warnings
    for warning_time, warning_msg in warnings:
        wait_time = timeout_seconds - warning_time
        if wait_time > 0:
            await asyncio.sleep(wait_time)
            
            # Check if order still pending
            order = await db.get_order(order_id)
            if order and order['status'] == 'pending':
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"{warning_msg}\n\n🆔 Order: `{order_id}`",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass  # User might have blocked bot
    
    # Wait for final expiry
    await asyncio.sleep(60)
    
    # Check if order is still pending
    order = await db.get_order(order_id)
    if order and order['status'] == 'pending':
        await db.update_order(order_id, {"status": "expired"})
        
        # Notify user with helpful message
        try:
            await bot.send_message(
                chat_id,
                f"⏰ **Payment Time Expired**\n\n"
                f"Order `{order_id}` has expired.\n\n"
                f"Don't worry! You can create a new order anytime.\n"
                f"Just tap **💸 Start Payment** from the main menu.\n\n"
                f"💡 Tip: Complete payment within {PAYMENT_TIMEOUT_MINUTES} minutes next time.",
                parse_mode="Markdown"
            )
        except Exception:
            pass

@router.callback_query(F.data.startswith("upload_proof:"))
async def request_screenshot(callback: CallbackQuery, state: FSMContext):
    """Request payment screenshot from user (optimized)"""
    # INSTANT FEEDBACK
    await callback.answer("📸 Please upload screenshot...")
    
    order_id = callback.data.split(":")[1]
    
    # Check order status
    order = await db.get_order(order_id)
    if not order:
        await callback.message.answer("❌ Order not found. Please contact support.")
        return
    
    if order['status'] == 'expired':
        await callback.message.answer(
            "⏰ **Order Expired**\n\n"
            "This order has expired. Please create a new order.",
            parse_mode="Markdown"
        )
        return
    
    if order['status'] != 'pending':
        await callback.message.answer(
            "ℹ️ **Order Already Processed**\n\n"
            "This order is already being processed or completed.",
            parse_mode="Markdown"
        )
        return
    
    # Set FSM state
    await state.set_state(PaymentStates.waiting_for_screenshot)
    await state.update_data(order_id=order_id)
    
    await callback.message.answer(
        "📸 **Upload Payment Screenshot**\n\n"
        "Please send a clear screenshot of your payment confirmation.\n\n"
        "⚠️ **Make sure the screenshot shows:**\n"
        "• Transaction amount\n"
        "• UPI transaction ID\n"
        "• Date and time\n\n"
        "💡 Send the image now...",
        parse_mode="Markdown"
    )

@router.message(PaymentStates.waiting_for_screenshot, F.photo)
async def handle_screenshot(message: Message, state: FSMContext):
    """Process uploaded payment screenshot"""
    data = await state.get_data()
    order_id = data.get("order_id")
    
    if not order_id:
        await message.answer("❌ Error: Order ID not found. Please try again.")
        await state.clear()
        return
    
    # Get the highest quality photo
    photo = message.photo[-1]
    file_id = photo.file_id
    
    # Update order with screenshot
    await db.update_order(order_id, {
        "status": "verification",
        "payment_screenshot": file_id
    })
    
    # Notify user
    await message.answer(
        "✅ **Screenshot Received!**\n\n"
        "Your payment is being verified by our team.\n"
        "You'll be notified once approved (usually within 5-10 minutes)."
    )
    
    # Forward to admin
    order = await db.get_order(order_id)
    admin_text = (
        f"🔔 **New Payment Verification Request**\n\n"
        f"👤 User: {message.from_user.first_name} (@{message.from_user.username or 'N/A'})\n"
        f"🆔 User ID: `{message.from_user.id}`\n"
        f"📦 Order ID: `{order_id}`\n"
        f"🛍️ Service: **{order['service_name']}**\n"
        f"⏱️ Plan: **{order['plan_duration']}**\n"
        f"💰 Amount: **{format_currency(order['amount'])}**\n\n"
        f"⬇️ Payment Screenshot:"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_photo(
                chat_id=admin_id,
                photo=file_id,
                caption=admin_text,
                reply_markup=get_admin_approval_buttons(order_id),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Failed to send to admin {admin_id}: {e}")
    
    await state.clear()

@router.callback_query(F.data.startswith("cancel_order:"))
async def cancel_order(callback: CallbackQuery):
    """Cancel pending order"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    order_id = callback.data.split(":")[1]
    
    await db.update_order(order_id, {"status": "cancelled"})
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    
    await callback.message.edit_caption(
        caption=f"❌ Order `{order_id}` has been cancelled.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer("Order cancelled")


# Free subscription handlers
class FreeSubscriptionStates(StatesGroup):
    waiting_for_email = State()


@router.callback_query(F.data.startswith("confirm_free:"))
async def confirm_free_subscription(callback: CallbackQuery, state: FSMContext):
    """Handle free subscription confirmation"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    parts = callback.data.split(":")
    service_id = parts[1]
    plan_duration = parts[2]
    
    service = get_service(service_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    
    # Request email
    await callback.message.edit_text(
        f"✅ *Activating FREE YouTube Premium*\n\n"
        f"📧 Please send your *Gmail address*\n"
        f"(the email you want to use for YouTube Premium)\n\n"
        f"Example: yourname@gmail.com",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    # Set state to wait for email
    await state.set_state(FreeSubscriptionStates.waiting_for_email)
    await state.update_data(service_id=service_id, plan_duration=plan_duration)
    await callback.answer()


@router.message(FreeSubscriptionStates.waiting_for_email)
async def receive_free_email(message: Message, state: FSMContext):
    """Receive email for free subscription"""
    email = message.text.strip()
    data = await state.get_data()
    
    # Create free order
    order_data = {
        "user_id": message.from_user.id,
        "username": message.from_user.username or message.from_user.first_name,
        "service_id": data['service_id'],
        "service_name": "YouTube Premium",
        "plan_duration": data['plan_duration'],
        "amount": 0,  # FREE
        "status": "approved",  # Auto-approve free orders
        "user_details": email
    }
    
    order_id = await db.create_order(order_data)
    
    # Notify user
    await message.answer(
        "🎉 *FREE Subscription Activated!*\n\n"
        f"✅ Service: YouTube Premium\n"
        f"📧 Email: {email}\n"
        f"⏱️ Duration: 1 Month FREE\n\n"
        "📬 You'll receive the invitation link within 24 hours!\n\n"
        "💡 After your free month, renew for just ₹25/month!",
        parse_mode="Markdown"
    )
    
    # Notify admin
    admin_text = (
        f"🎁 *NEW FREE SUBSCRIPTION*\n\n"
        f"👤 User: {message.from_user.first_name}\n"
        f"🆔 User ID: `{message.from_user.id}`\n"
        f"📦 Order ID: `{order_id}`\n"
        f"🛍️ Service: YouTube Premium (FREE)\n"
        f"📧 Email: {email}\n\n"
        f"⚠️ Send invitation link to user!"
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
