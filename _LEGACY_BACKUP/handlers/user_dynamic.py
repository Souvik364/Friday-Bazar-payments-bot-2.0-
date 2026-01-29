"""
Dynamic User Handlers
=====================
New handlers that use the dynamic menu system
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database.db_manager import db
from core.menu_renderer import render_menu
from core.action_handler import handle_callback

router = Router()


@router.message(Command("start"))
async def cmd_start_dynamic(message: Message):
    """
    Handle /start command - Dynamic menu version
    Shows main menu from database
    """
    # Check for referral code
    args = message.text.split()
    referrer_id = None
    
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
            user_id = message.from_user.id
            
            # Don't allow self-referral
            if referrer_id == user_id:
                referrer_id = None
        except ValueError:
            pass
    
    # Get or create user
    user = await db.get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        referrer_id=referrer_id
    )
    
    # Send referral confirmation if applicable
    if referrer_id and user.referrer_id == referrer_id:
        await message.answer(f"✅ You've been referred by user {referrer_id}!")
    
    # Load and render main menu from database
    main_menu = await db.get_menu_by_name("Main Menu")
    
    if not main_menu:
        # Fallback message if menu not found
        await message.answer(
            "⚠️ Bot is being set up. Please contact admin.\n\n"
            "Run: python -m database.migrations.seed_default_data"
        )
        return
    
    # Render the menu
    await render_menu(
        user_id=user.user_id,
        menu_id=main_menu.menu_id,
        bot=message.bot,
        chat_id=message.chat.id
    )


@router.callback_query()
async def callback_query_handler(callback: CallbackQuery):
    """
    Universal callback handler - routes all button clicks
    """
    await handle_callback(callback, callback.bot)


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Show main menu again"""
    main_menu = await db.get_menu_by_name("Main Menu")
    if main_menu:
        await render_menu(
            user_id=message.from_user.id,
            menu_id=main_menu.menu_id,
            bot=message.bot,
            chat_id=message.chat.id
        )
    else:
        await message.answer("Main menu not found!")
