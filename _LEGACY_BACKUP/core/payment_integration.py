"""
Payment Integration
===================
Integrates dynamic menu system with existing payment flow
"""

from aiogram import Bot
from aiogram.types import CallbackQuery
from database.db_manager import db


async def handle_payment_confirmation(callback: CallbackQuery, plan_id: str, bot: Bot) -> bool:
    """Handle payment confirmation and QR generation"""
    # Get payment plan
    plan = await db.get_plan(plan_id)
    if not plan:
        await callback.answer("Payment plan not found!")
        return False
    
    # Import required modules for payment
    from src.utils.helpers import generate_upi_qr, format_currency, get_expiry_time
    from src.config import UPI_ID, UPI_NAME, PAYMENT_TIMEOUT_MINUTES
    from src.keyboards.menus import get_payment_verification_buttons
    from src.services.db import db as legacy_db
    import uuid
    import asyncio
    
    # Create order ID
    order_id = str(uuid.uuid4())[:8]
    
    # Create order in legacy database
    order_data = {
        "user_id": callback.from_user.id,
        "username": callback.from_user.username or callback.from_user.first_name,
        "service_id": plan.plan_id,  # Use plan_id as service_id
        "service_name": plan.name,
        "plan_duration": f"{plan.duration_days} days",
        "amount": plan.price,
        "payment_screenshot": None,
        "user_details": None
    }
    
    order_id = await legacy_db.create_order(order_data)
    
    # Generate QR code
    qr_image = generate_upi_qr(UPI_ID, UPI_NAME, plan.price, order_id)
    
    # Payment instruction message
    expiry_time = get_expiry_time(PAYMENT_TIMEOUT_MINUTES)
    payment_text = (
        f"💳 **Payment Details**\n\n"
        f"🛍️ Service: **{plan.name}**\n"
        f"⏱️ Plan: **{plan.duration_days} days**\n"
        f"💰 Amount: **{format_currency(plan.price)}**\n"
        f"🆔 Order ID: `{order_id}`\n\n"
        f"⏰ Complete payment before **{expiry_time}**\n"
        f"({PAYMENT_TIMEOUT_MINUTES} minutes)\n\n"
        f"📲 **Scan the QR code** or pay to:\n"
        f"UPI ID: `{UPI_ID}`\n\n"
        f"⚠️ **Important:**\n"
        f"• Use the exact amount shown\n"
        f"• Keep your payment screenshot ready\n"
        f"• Click 'I've Paid' after completing payment"
    )
    
    # Delete the plan details message
    try:
        await callback.message.delete()
    except:
        pass
    
    # Send QR code with instructions
    await bot.send_photo(
        chat_id=callback.message.chat.id,
        photo=qr_image,
        caption=payment_text,
        reply_markup=get_payment_verification_buttons(order_id),
        parse_mode="Markdown"
    )
    
    # Start payment timer
    asyncio.create_task(start_payment_timer(order_id, callback.from_user.id, callback.message.chat.id, bot))
    
    await callback.answer("✅ Payment QR generated!")
    return True


async def start_payment_timer(order_id: str, user_id: int, chat_id: int, bot: Bot):
    """Async timer for payment expiration"""
    from src.config import PAYMENT_TIMEOUT_MINUTES
    from src.services.db import db as legacy_db
    
    await asyncio.sleep(PAYMENT_TIMEOUT_MINUTES * 60)
    
    # Check if order is still pending
    order = await legacy_db.get_order(order_id)
    if order and order['status'] == 'pending':
        await legacy_db.update_order(order_id, {"status": "expired"})
        
        try:
            await bot.send_message(
                chat_id,
                f"⏰ **Payment Expired**\n\n"
                f"Order `{order_id}` has expired.\n"
                f"Please create a new order if you still want to purchase.",
                parse_mode="Markdown"
            )
        except:
            pass


