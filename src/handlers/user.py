"""
Friday Bazar Payments - User Handler
=====================================
Consolidated user-facing commands: start, help, status, cancel
"""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.keyboards.menus import get_main_menu
from src.services.db import db
from src.services.subscription import subscription_service
from src.config import BOT_NAME, SUPPORT_USERNAME
from src.utils.helpers import format_currency

router = Router()

# Auto-delete timeout in seconds
AUTO_DELETE_TIMEOUT = 60

async def auto_delete_message(message: Message, delay: int):
    """Automatically delete a message after specified delay"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        # Message might already be deleted or bot doesn't have permission
        pass


@router.message(Command("start"))
async def cmd_start(message: Message, lang: str = "en", t=None):
    """
    Handle /start command and referral links
    Format: /start or /start ref_123456
    """
    # Check for referral code
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = int(args[1].replace("ref_", ""))
        user_id = message.from_user.id
        
        # Don't allow self-referral
        if referrer_id != user_id:
            success = await db.set_referrer(user_id, referrer_id)
            if success:
                await message.answer(
                    f"✅ You've been referred by user {referrer_id}!"
                )
    
    # Ensure user exists in database
    await db.get_user(message.from_user.id)
    
    # Welcome message matching the image
    first_name = message.from_user.first_name or "User"
    welcome_text = (
        "━━━━━━━━━━━━━━━━━\n"
        "🎉 **Welcome to Friday Bazar!**\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "Your one-stop shop for premium subscriptions at unbeatable prices! 💎\n\n"
        "👇 **Choose an option below:**"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu()
    )


@router.message(Command("help"))
@router.message(F.text == "🆘 Help")
async def cmd_help(message: Message, lang: str = "en", t=None):
    """Help command - show how to use the bot"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    help_text = (
        "🆘 *Help & Support*\n\n"
        
        "*How to Purchase:*\n"
        "1️⃣ Tap 🛒 Start Payment\n"
        "2️⃣ Choose your service\n"
        "3️⃣ Select plan duration\n"
        "4️⃣ Pay via UPI & upload screenshot\n"
        "5️⃣ Wait for approval (5-10 mins)\n"
        "6️⃣ Receive your credentials\n\n"
        
        "*Referral Program:*\n"
        "• Share your link from 🔗 Referral Link\n"
        "• Earn 10% on each purchase\n"
        "• Track earnings in 💰 My Friday Coins\n\n"
        
        "Need assistance? Tap 📞 Contact\n\n"
        "⏰ _This message will auto-delete in 60 seconds_"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Close", callback_data="close_msg")]
    ])
    
    sent_message = await message.answer(help_text, reply_markup=keyboard, parse_mode="Markdown")
    
    # Schedule auto-delete
    asyncio.create_task(auto_delete_message(sent_message, AUTO_DELETE_TIMEOUT))


@router.message(Command("status"))
async def cmd_status(message: Message, lang: str = "en", t=None):
    """Show user status - subscription and coins"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    sub_info = await subscription_service.get_subscription_info(user_id)
    
    status_text = "📊 *Your Dashboard*\n\n"
    
    # Subscription
    status_text += "*Subscription Status:*\n"
    if sub_info['is_active']:
        days_emoji = "🟢" if sub_info['days_remaining'] > 7 else "🟡" if sub_info['days_remaining'] > 3 else "🔴"
        status_text += (
            f"✅ Active Premium\n"
            f"📦 {sub_info['service']} - {sub_info['plan']}\n"
            f"📅 Expires: {sub_info['expiry_date'].strftime('%d %b %Y')}\n"
            f"{days_emoji} {sub_info['days_remaining']} days remaining\n\n"
        )
    else:
        status_text += (
            "🔓 No active subscription\n"
            "Tap 🛒 Start Payment to subscribe\n\n"
        )
    
    # Earnings
    status_text += "*Your Earnings:*\n"
    status_text += (
        f"💰 Balance: ₹{format_currency(user['coins'])}\n"
        f"👥 Referrals: {user['total_referrals']}\n"
        f"💵 Total Earned: ₹{format_currency(user['total_earned'])}\n"
    )
    
    await message.answer(status_text, parse_mode="Markdown")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, lang: str = "en", t=None):
    """Cancel current operation"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("ℹ️ No active operation to cancel.")
        return
    
    await state.clear()
    await message.answer("✅ Operation canceled.")


@router.message(F.text == "📞 Contact")
async def contact_support(message: Message, lang: str = "en", t=None):
    """Contact support button handler"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    contact_text = (
        "📞 *Support Center*\n\n"
        
        f"Contact our support team:\n"
        f"👉 @{SUPPORT_USERNAME}\n\n"
        
        "*Support Hours:*\n"
        "Mon-Sat: 9 AM - 9 PM IST\n"
        "Sunday: 10 AM - 6 PM IST\n\n"
        
        "💡 *For faster support:*\n"
        "• Include your User ID\n"
        "• Describe the issue clearly\n"
        "• Attach relevant screenshots\n\n"
        
        "Average response: 30 minutes\n\n"
        "⏰ _This message will auto-delete in 60 seconds_"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Close", callback_data="close_msg")]
    ])
    
    sent_message = await message.answer(contact_text, reply_markup=keyboard, parse_mode="Markdown")
    
    # Schedule auto-delete
    asyncio.create_task(auto_delete_message(sent_message, AUTO_DELETE_TIMEOUT))


# New callback handlers for inline keyboard buttons
@router.callback_query(F.data == "start_payment")
async def callback_start_payment(callback: CallbackQuery):
    """Handle Start Payment inline button"""
    # INSTANT FEEDBACK
    await callback.answer("⏳ Loading services...")
    
    from src.keyboards.menus import get_services_grid
    
    await callback.message.edit_text(
        "🛒 *Choose a Service*\n\nSelect the premium service you want to purchase:",
        reply_markup=get_services_grid(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "telegram_accounts")
async def callback_telegram_accounts(callback: CallbackQuery):
    """Handle Telegram Accounts inline button"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    accounts_text = (
        "📱 *Telegram Premium Accounts*\n\n"
        "🚧 Coming Soon!\n\n"
        "We're working on bringing you Telegram Premium accounts at unbeatable prices.\n\n"
        "Stay tuned for updates! 🎉"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    
    await callback.message.edit_text(accounts_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "terms_of_service")
async def callback_terms_of_service(callback: CallbackQuery):
    """Handle Terms of Service inline button"""
    terms_text = (
        "📜 *Terms of Service*\n\n"
        
        "*1. Service Delivery*\n"
        "• Premium subscription access provided\n"
        "• Activation within 24 hours\n"
        "• Valid credentials & full access\n"
        "• All sales are final\n\n"
        
        "*2. Payment Policy*\n"
        "• UPI payments only\n"
        "• Complete within 10 minutes\n"
        "• Screenshot required\n\n"
        
        "*3. Referral Program*\n"
        "• Earn 10% per referral\n"
        "• No self-referrals allowed\n"
        "• Coins credited after approval\n\n"
        
        "*4. Account Usage*\n"
        "⚠️ Do not change passwords\n"
        "⚠️ Respect account sharing limits\n"
        "⚠️ Violations = suspension\n\n"
        
        f"Questions? Contact @{SUPPORT_USERNAME}"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    
    await callback.message.edit_text(terms_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


# Back to main menu handler
@router.callback_query(F.data == "back_to_main_menu")
async def callback_back_to_main_menu(callback: CallbackQuery):
    """Return to main menu"""
    from src.keyboards.menus import get_main_menu
    
    first_name = callback.from_user.first_name or "User"
    welcome_text = (
        "━━━━━━━━━━━━━━━━━\n"
        "🎉 **Welcome to Friday Bazar!**\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "Your one-stop shop for premium subscriptions at unbeatable prices! 💎\n\n"
        "👇 **Choose an option below:**"
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


# Universal callback handler for action: prefixed callbacks
@router.callback_query(F.data.startswith("action:"))
async def callback_action_handler(callback: CallbackQuery):
    """Route action callbacks to action_handler module"""
    from src.handlers.action_handler import handle_callback
    await handle_callback(callback, callback.bot)


@router.message(F.text == "📄 Terms of Service")
async def show_terms(message: Message):
    """Terms of Service button handler"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    terms_text = (
        "📄 *Terms of Service*\n\n"
        
        "*1. Service Delivery*\n"
        "• Premium subscription access provided\n"
        "• Activation within 24 hours\n"
        "• Valid credentials & full access\n"
        "• All sales are final\n\n"
        
        "*2. Payment Policy*\n"
        "• UPI payments only\n"
        "• Complete within 10 minutes\n"
        "• Screenshot required\n\n"
        
        "*3. Referral Program*\n"
        "• Earn 10% per referral\n"
        "• No self-referrals allowed\n"
        "• Coins credited after approval\n\n"
        
        "*4. Account Usage*\n"
        "⚠️ Do not change passwords\n"
        "⚠️ Respect account sharing limits\n"
        "⚠️ Violations = suspension\n\n"
        
        f"Questions? Contact @{SUPPORT_USERNAME}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Close", callback_data="close_msg")]
    ])
    
    await message.answer(terms_text, reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data == "close_msg")
async def close_message(callback: CallbackQuery):
    """Delete message when Close button is clicked"""
    await callback.message.delete()
    await callback.answer()

