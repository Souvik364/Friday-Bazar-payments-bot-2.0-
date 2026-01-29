"""
Friday Bazar Payments - Action Handler
=======================================
Routes button clicks for user actions (coins, referral, help, etc.)
"""

from aiogram import Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from src.services.db import db
from src.config import SUPPORT_USERNAME, BOT_USERNAME
from src.utils.helpers import format_currency

async def handle_callback(callback: CallbackQuery, bot: Bot) -> bool:
    """
    Main callback handler routing for 'action:' prefixed callbacks
    
    Callback data format: "action:action_name"
    """
    try:
        # Parse callback data
        if ":" not in callback.data:
            await callback.answer("Invalid action")
            return False
        
        _, action_name = callback.data.split(":", 1)
        
        if action_name == "show_coins":
            return await show_coins(callback)
        
        elif action_name == "show_referral":
            return await show_referral(callback)
        
        elif action_name == "show_help":
            return await show_help(callback)
        
        elif action_name == "show_contact":
            return await show_contact(callback)
        
        else:
            await callback.answer(f"Action '{action_name}' not implemented yet")
            return False
        
    except Exception as e:
        print(f"[ERROR] Callback handling failed: {e}")
        await callback.answer("An error occurred.")
        return False


async def show_coins(callback: CallbackQuery) -> bool:
    """Show user's coin balance"""
    user = await db.get_user(callback.from_user.id)
    
    if not user:
        await callback.answer("User not found!")
        return False
    
    message = (
        "💰 **Your Friday Coins**\n\n"
        f"**Balance:** ₹{format_currency(user.get('coins', 0))}\n"
        f"**Total Earnings:** ₹{format_currency(user.get('total_earned', 0))}\n"
        f"**Total Referrals:** {user.get('total_referrals', 0)}\n\n"
        "💡 _1 Coin = ₹1_\n\n"
        "Earn more by referring friends! You get 10% of their purchase amount."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    
    await callback.message.edit_text(message, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
    return True


async def show_referral(callback: CallbackQuery) -> bool:
    """Show user's referral link"""
    user_id = callback.from_user.id
    
    referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    
    message = (
        "🔗 **Your Referral Link**\n\n"
        "Share this link with friends:\n"
        f"`{referral_link}`\n\n"
        "**How it works:**\n"
        "✅ Friend clicks your link\n"
        "✅ Friend makes a purchase\n"
        "✅ You earn 10% coins instantly!\n\n"
        "💰 **Example:** Friend buys ₹100 plan → You get ₹10"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Sub Share", url=f"https://t.me/share/url?url={referral_link}&text=Get%20Premium%20Subscriptions%20at%20Friday%20Bazar!")],
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    
    await callback.message.edit_text(message, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
    return True


async def show_help(callback: CallbackQuery) -> bool:
    """Show help information"""
    message = (
        "🆘 **Help & Support**\n\n"
        "**How to Buy:**\n"
        "1️⃣ Click '🛒 Start Payment'\n"
        "2️⃣ Choose your service\n"
        "3️⃣ Pay via UPI and upload screenshot\n"
        "4️⃣ Get instant access!\n\n"
        "**Payment Methods:**\n"
        "💳 UPI (PhonePe, GPay, Paytm)\n\n"
        "**Delivery Time:**\n"
        "⚡ Within 5-30 minutes after verification\n\n"
        "**Need Help?**\n"
        "📞 Click 'Contact Support' for assistance"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    
    await callback.message.edit_text(message, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
    return True


async def show_contact(callback: CallbackQuery) -> bool:
    """Show contact information"""
    
    message = (
        "📞 **Contact Support**\n\n"
        "For any queries, issues, or support:\n\n"
        f"👤 @{SUPPORT_USERNAME}\n\n"
        "**Support Hours:**\n"
        "🕐 24/7 Available\n\n"
        "**Response Time:**\n"
        "⚡ Usually within 1 hour\n\n"
        "We're here to help! 😊"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    
    await callback.message.edit_text(message, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
    return True
