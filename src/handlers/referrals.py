"""
Friday Bazar Payments - Referral Handler
=========================================
Handles referral link generation and coin stats display
"""

import asyncio
from aiogram import Router, F
from aiogram.types import Message

from src.services.db import db
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


@router.message(F.text == "🔗 Referral Link")
async def show_referral_link(message: Message):
    """Show user's referral link with clean design"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    bot_username = (await message.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = (
        "🎁 *Your Referral Link*\n\n"
        
        f"`{referral_link}`\n\n"
        
        "📊 *Your Stats:*\n"
        f"💰 Balance: ₹{format_currency(user.get('coins', 0))}\n"
        f"👥 Referrals: {user.get('total_referrals', 0)}\n"
        f"💵 Earned: ₹{format_currency(user.get('total_earned', 0))}\n\n"
        
        "*How it works:*\n"
        "1. Share your link\n"
        "2. Friends join & purchase\n"
        "3. You earn 10% instantly\n\n"
        
        "✅ Commission credited after approval\n\n"
        "⏰ _This message will auto-delete in 60 seconds_"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Close", callback_data="close_msg")]
    ])
    
    sent_message = await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    # Schedule auto-delete
    asyncio.create_task(auto_delete_message(sent_message, AUTO_DELETE_TIMEOUT))


@router.message(F.text == "💰 My Friday Coins")
async def show_coin_balance(message: Message):
    """Show user's coin balance with clean design"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    balance = user.get('coins', 0)
    total_earned = user.get('total_earned', 0)
    total_referrals = user.get('total_referrals', 0)
    
    text = (
        "💰 *Friday Coins Wallet*\n\n"
        
        f"*Current Balance:*\n"
        f"₹{format_currency(balance)}\n\n"
        
        "*Your Earnings:*\n"
        f"👥 Referrals: {total_referrals}\n"
        f"💵 Lifetime: ₹{format_currency(total_earned)}\n"
        f"📥 Withdrawable: ₹{format_currency(balance)}\n\n"
        
        "*Note:*\n"
        "• Minimum withdrawal: ₹100\n"
        "• 1 Coin = ₹1\n"
        "• Contact support to withdraw\n\n"
        
        "Share 🔗 Referral Link to earn more!\n\n"
        "⏰ _This message will auto-delete in 60 seconds_"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Close", callback_data="close_msg")]
    ])
    
    sent_message = await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    # Schedule auto-delete
    asyncio.create_task(auto_delete_message(sent_message, AUTO_DELETE_TIMEOUT))
