"""
Friday Bazar Payments - Additional Menu Handlers
=================================================
Handles Telegram Accounts button only (other buttons in user.py)
"""

from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text == "📱 Telegram Accounts")
async def telegram_accounts(message: Message):
    """Telegram accounts button handler"""
    accounts_text = (
        "📱 *Telegram Premium Accounts*\n\n"
        "🚧 Coming Soon!\n\n"
        "We're working on bringing you Telegram Premium accounts at unbeatable prices.\n\n"
        "Stay tuned for updates! 🎉"
    )
    
    await message.answer(accounts_text, parse_mode="Markdown")
