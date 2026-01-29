"""
Friday Bazar Payments - Catalog Handler
========================================
Handles service grid menu and product details
"""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from src.keyboards.menus import get_main_menu, get_services_grid, get_plan_buttons
from src.keyboards.menus import get_main_menu, get_services_grid, get_plan_buttons
from src.data.services import get_service
from src.config import BOT_NAME

router = Router()

# Auto-delete timeout in seconds (60 seconds = 1 minute)
AUTO_DELETE_TIMEOUT = 60

async def auto_delete_message(message: Message, delay: int):
    """Automatically delete a message after specified delay"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        # Message might already be deleted or bot doesn't have permission
        pass

@router.message(F.text == "🛒 Start Payment")
async def show_services(message: Message):
    """Show service grid when Start Payment button is clicked"""
    sent_message = await message.answer(
        "━━━━━━━━━━━━━━━━━\n"
        "📦 **Available Services**\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "Select a service to view plans:\n\n"
        "⏰ _This message will auto-delete in 60 seconds_",
        reply_markup=get_services_grid(),
        parse_mode="Markdown"
    )
    
    # Schedule auto-delete
    asyncio.create_task(auto_delete_message(sent_message, AUTO_DELETE_TIMEOUT))

@router.callback_query(F.data == "back_to_services")
async def back_to_services(callback: CallbackQuery):
    """Return to services grid"""
    # INSTANT FEEDBACK
    await callback.answer()
    
    await callback.message.edit_text(
        "━━━━━━━━━━━━━━━━━\n"
        "📦 **Available Services**\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "Select a service to view plans:",
        reply_markup=get_services_grid(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("service:"))
async def show_service_details(callback: CallbackQuery):
    """Show service details and price buttons"""
    # INSTANT FEEDBACK
    await callback.answer("⏳ Loading...")
    
    service_id = callback.data.split(":")[1]
    service = get_service(service_id)
    
    if not service:
        await callback.message.edit_text("❌ Service not found. Please try again.")
        return
    
    # Show plans for ALL services (demo check happens on purchase)
    message_text = f"{service['emoji']} **{service['name']}**\n\n"
    message_text += service['instruction']
    message_text += "\n\n💰 **Select a Plan:**"
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_plan_buttons(service_id),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Return to main menu"""
    first_name = callback.from_user.first_name or "User"
    welcome_text = (
        f"Hey, {first_name}..\n\n"
        "🌟 Welcome to Friday Bazar Payment Bot!\n"
        "🌟\n"
        "📜 Securely make payments using UPI!\n\n"
        "👇 Choose an option below:"
    )
    
    try:
        # Try to edit the current message
        if callback.message.photo:
            # If it's a photo message, delete it and send new text message
            await callback.message.delete()
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text=welcome_text,
                reply_markup=get_main_menu()
            )
        else:
            # If it's a text message, edit it
            await callback.message.edit_text(
                welcome_text,
                reply_markup=get_main_menu()
            )
    except Exception as e:
        # If edit fails for any reason, delete and send new message
        try:
            await callback.message.delete()
        except:
            pass
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=welcome_text,
            reply_markup=get_main_menu()
        )
    
    await callback.answer()
