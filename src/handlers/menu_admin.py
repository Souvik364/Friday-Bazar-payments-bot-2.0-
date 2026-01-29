"""
Friday Bazar Payments - Dynamic Menu Admin
===========================================
Admin commands to manage dynamic menu buttons at runtime
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import aiofiles
import json
from pathlib import Path

from src.config import ADMIN_IDS

router = Router()

# Menus file path
MENUS_FILE = Path("data/menus.json")


async def load_menus() -> dict:
    """Load custom menus from JSON file"""
    if not MENUS_FILE.exists():
        return {"custom_buttons": []}
    
    async with aiofiles.open(MENUS_FILE, 'r', encoding='utf-8') as f:
        content = await f.read()
        return json.loads(content) if content else {"custom_buttons": []}


async def save_menus(menus: dict):
    """Save menus to JSON file"""
    MENUS_FILE.parent.mkdir(exist_ok=True)
    async with aiofiles.open(MENUS_FILE, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(menus, indent=2, ensure_ascii=False))


@router.message(Command("menu_add"))
async def add_menu_button(message: Message):
    """Add custom menu button (admin only)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Admin access required.")
        return
    
    # Parse: /menu_add Button Text|action_id
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or '|' not in parts[1]:
        await message.answer(
            "❌ **Usage:**\n"
            "`/menu_add Button Text|action_id`\n\n"
            "Example:\n"
            "`/menu_add 🎮 Gaming Accounts|gaming_accounts`",
            parse_mode="Markdown"
        )
        return
    
    button_text, action = parts[1].split('|', 1)
    button_text = button_text.strip()
    action = action.strip()
    
    menus = await load_menus()
    menus["custom_buttons"].append({
        "text": button_text,
        "action": action
    })
    await save_menus(menus)
    
    await message.answer(
        f"✅ **Button Added**\n\n"
        f"Text: {button_text}\n"
        f"Action: `{action}`\n\n"
        f"⚠️ **Note:** Bot restart required for changes to take effect.",
        parse_mode="Markdown"
    )


@router.message(Command("menu_remove"))
async def remove_menu_button(message: Message):
    """Remove custom menu button (admin only)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Admin access required.")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "❌ **Usage:**\n"
            "`/menu_remove action_id`",
            parse_mode="Markdown"
        )
        return
    
    action_to_remove = parts[1].strip()
    menus = await load_menus()
    
    original_count = len(menus["custom_buttons"])
    menus["custom_buttons"] = [
        btn for btn in menus["custom_buttons"]
        if btn["action"] != action_to_remove
    ]
    
    if len(menus["custom_buttons"]) < original_count:
        await save_menus(menus)
        await message.answer(
            f"✅ Button removed.\n\n"
            f"⚠️ **Note:** Bot restart required for changes to take effect.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"❌ Button with action `{action_to_remove}` not found.", parse_mode="Markdown")


@router.message(Command("menu_list"))
async def list_menu_buttons(message: Message):
    """List all custom menu buttons (admin only)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Admin access required.")
        return
    
    menus = await load_menus()
    
    if not menus["custom_buttons"]:
        await message.answer("ℹ️ No custom menu buttons configured.")
        return
    
    list_text = "📋 **Custom Menu Buttons**\n\n"
    for btn in menus["custom_buttons"]:
        list_text += f"• {btn['text']} (`{btn['action']}`)\n"
    
    await message.answer(list_text, parse_mode="Markdown")
