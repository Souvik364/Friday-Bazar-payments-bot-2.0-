# Free month confirmation handler
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.services.db import db
from src.data.services import get_service
from src.config import ADMIN_IDS

# Add to payment.py or create separate handler
class FreeSubscriptionStates(StatesGroup):
    waiting_for_email = State()

@router.callback_query(F.data.startswith("confirm_free:"))
async def confirm_free_subscription(callback: CallbackQuery, state: FSMContext):
    """Handle free subscription confirmation"""
    parts = callback.data.split(":")
    service_id = parts[1]
    plan_duration = parts[2]
    
    service = get_service(service_id)
    
    # Request email
    await callback.message.edit_text(
        f"✅ *Activating FREE YouTube Premium*\n\n"
        f"📧 Please send your *Gmail address*\n"
        f"(the email you want to use for YouTube Premium)\n\n"
        f"Example: yourname@gmail.com",
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
