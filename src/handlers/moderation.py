"""
Friday Bazar Payments - Moderation Handler
===========================================
Keyword auto-reply system and moderation commands
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import aiofiles
import json
from pathlib import Path

from src.config import ADMIN_IDS

router = Router()

# Keywords file path
KEYWORDS_FILE = Path("data/keywords.json")


async def load_keywords() -> dict:
    """Load keywords from JSON file"""
    if not KEYWORDS_FILE.exists():
        return {}
    
    async with aiofiles.open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
        content = await f.read()
        return json.loads(content) if content else {}


async def save_keywords(keywords: dict):
    """Save keywords to JSON file"""
    KEYWORDS_FILE.parent.mkdir(exist_ok=True)
    async with aiofiles.open(KEYWORDS_FILE, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(keywords, indent=2, ensure_ascii=False))


@router.message(Command("mod_keyword_add"))
async def add_keyword(message: Message):
    """Add keyword auto-reply (admin only)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Admin access required.")
        return
    
    # Parse: /mod_keyword_add keyword|reply
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or '|' not in parts[1]:
        await message.answer(
            "❌ **Usage:**\n"
            "`/mod_keyword_add keyword|reply`\n\n"
            "Example:\n"
            "`/mod_keyword_add price|Check our catalog with /start!`",
            parse_mode="Markdown"
        )
        return
    
    keyword, reply = parts[1].split('|', 1)
    keyword = keyword.strip().lower()
    reply = reply.strip()
    
    keywords = await load_keywords()
    keywords[keyword] = reply
    await save_keywords(keywords)
    
    await message.answer(
        f"✅ **Keyword Added**\n\n"
        f"Trigger: `{keyword}`\n"
        f"Reply: {reply}",
        parse_mode="Markdown"
    )


@router.message(Command("mod_keyword_remove"))
async def remove_keyword(message: Message):
    """Remove keyword (admin only)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Admin access required.")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "❌ **Usage:**\n"
            "`/mod_keyword_remove keyword`",
            parse_mode="Markdown"
        )
        return
    
    keyword = parts[1].strip().lower()
    keywords = await load_keywords()
    
    if keyword in keywords:
        del keywords[keyword]
        await save_keywords(keywords)
        await message.answer(f"✅ Keyword `{keyword}` removed.", parse_mode="Markdown")
    else:
        await message.answer(f"❌ Keyword `{keyword}` not found.", parse_mode="Markdown")


@router.message(Command("mod_keyword_list"))
async def list_keywords(message: Message):
    """List all keywords (admin only)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Admin access required.")
        return
    
    keywords = await load_keywords()
    
    if not keywords:
        await message.answer("ℹ️ No keywords configured.")
        return
    
    list_text = "📋 **Keyword Auto-Replies**\n\n"
    for keyword, reply in keywords.items():
        list_text += f"• `{keyword}` → {reply}\n"
    
    await message.answer(list_text, parse_mode="Markdown")


@router.message(F.text)
async def check_keywords(message: Message):
    """
    Check all messages for keywords and auto-reply
    This handler should be registered LAST in the router chain
    """
    # Skip admin messages
    if message.from_user.id in ADMIN_IDS:
        return
    
    # Skip commands
    if message.text.startswith('/'):
        return
    
    keywords = await load_keywords()
    message_text = message.text.lower()
    
    # Check if any keyword matches
    for keyword, reply in keywords.items():
        if keyword in message_text:
            await message.answer(reply, parse_mode="Markdown")
            break  # Only reply to first match
