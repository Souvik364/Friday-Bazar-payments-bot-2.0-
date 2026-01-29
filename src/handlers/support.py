"""
Friday Bazar Payments - Support Handler
========================================
Support redirection with user ID auto-attachment
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from src.config import SUPPORT_USERNAME

router = Router()


@router.message(Command("support"))
async def cmd_support(message: Message,  lang: str = "en", t=None):
    """Support command - redirect to support with user info"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    support_text = (
        f"📞 **Contact Support**\n\n"
        f"Need assistance? Our support team is ready to help!\n\n"
        f"👤 Your User ID: `{user_id}`\n"
        f"📱 Click below to message support:\n\n"
        f"👉 @{SUPPORT_USERNAME}\n\n"
        f"💡 **Tip:** Mention your User ID when contacting support for faster assistance!\n\n"
        f"⏰ **Support Hours:**\n"
        f"Monday - Saturday: 9 AM - 9 PM IST\n"
        f"Sunday: 10 AM - 6 PM IST"
    )
    
    await message.answer(support_text, parse_mode="Markdown")
