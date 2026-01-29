"""
Menu Renderer
=============
Dynamic menu rendering engine that loads menus from database
"""

from typing import Optional, List
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.exceptions import TelegramBadRequest

from database.db_manager import db
from database.models import Menu, Button, ButtonType, UserSession, MenuContentType


# In-memory menu cache
_menu_cache = {}
_CACHE_TTL = 300  # 5 minutes


async def render_menu(user_id: int, menu_id: str, bot: Bot, chat_id: Optional[int] = None, 
                     message_id: Optional[int] = None, edit: bool = False) -> bool:
    """
    Render a menu from database and send to user
    
    Args:
        user_id: Telegram user ID
        menu_id: Menu ID to render
        bot: Bot instance
        chat_id: Chat ID (defaults to user_id)
        message_id: Message ID to edit (if edit=True)
        edit: Whether to edit existing message or send new one
    
    Returns:
        bool: Success status
    """
    if chat_id is None:
        chat_id = user_id
    
    # Fetch menu
    menu = await get_menu(menu_id)
    if not menu:
        await bot.send_message(chat_id, "❌ Menu not found. Please try again or contact support.")
        return False
    
    # Get buttons for menu
    buttons = await db.get_menu_buttons(menu_id)
    
    # Build keyboard
    keyboard = build_keyboard(buttons)
    
    # Update user session
    session = UserSession(
        user_id=user_id,
        current_menu_id=menu_id,
        state="browsing"
    )
    await db.update_user_session(session)
    
    # Send content based on type
    try:
        if edit and message_id:
            # Edit existing message
            await edit_menu_message(bot, chat_id, message_id, menu, keyboard)
        else:
            # Send new message
            await send_menu_message(bot, chat_id, menu, keyboard)
        
        return True
        
    except TelegramBadRequest as e:
        print(f"[ERROR] Failed to render menu {menu_id}: {e}")
        # Fallback: send as new message
        if edit:
            await send_menu_message(bot, chat_id, menu, keyboard)
        return False


async def get_menu(menu_id: str) -> Optional[Menu]:
    """Get menu from cache or database"""
    # For now, always fetch from DB (can add caching later)
    return await db.get_menu(menu_id)


def build_keyboard(buttons: List[Button]) -> InlineKeyboardMarkup:
    """
    Build InlineKeyboardMarkup from button list
    
    Buttons are organized by row and column
    """
    if not buttons:
        return InlineKeyboardMarkup(inline_keyboard=[])
    
    # Group buttons by row
    rows = {}
    for button in buttons:
        if button.row not in rows:
            rows[button.row] = []
        rows[button.row].append(button)
    
    # Sort rows
    sorted_rows = sorted(rows.items())
    
    # Build keyboard
    keyboard_rows = []
    for row_num, row_buttons in sorted_rows:
        # Sort buttons in row by column
        sorted_buttons = sorted(row_buttons, key=lambda b: b.column)
        
        keyboard_row = []
        for btn in sorted_buttons:
            # Create inline button based on type
            if btn.type == ButtonType.URL:
                # URL button
                keyboard_row.append(
                    InlineKeyboardButton(text=btn.text, url=btn.action_data)
                )
            else:
                # Callback button
                callback_data = f"{btn.type.value}:{btn.action_data}"
                keyboard_row.append(
                    InlineKeyboardButton(text=btn.text, callback_data=callback_data)
                )
        
        keyboard_rows.append(keyboard_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


async def send_menu_message(bot: Bot, chat_id: int, menu: Menu, keyboard: InlineKeyboardMarkup):
    """Send menu content based on type"""
    if menu.content_type == MenuContentType.TEXT:
        await bot.send_message(
            chat_id,
            menu.content_data,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    elif menu.content_type == MenuContentType.PHOTO:
        await bot.send_photo(
            chat_id,
            photo=menu.content_data,
            caption=menu.description or "",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    elif menu.content_type == MenuContentType.VIDEO:
        await bot.send_video(
            chat_id,
            video=menu.content_data,
            caption=menu.description or "",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    elif menu.content_type == MenuContentType.DOCUMENT:
        await bot.send_document(
            chat_id,
            document=menu.content_data,
            caption=menu.description or "",
            reply_markup=keyboard,
            parse_mode="HTML"
        )


async def edit_menu_message(bot: Bot, chat_id: int, message_id: int, 
                           menu: Menu, keyboard: InlineKeyboardMarkup):
    """Edit existing menu message"""
    if menu.content_type == MenuContentType.TEXT:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=menu.content_data,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        # For media messages, edit caption and keyboard
        await bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=menu.description or "",
            reply_markup=keyboard,
            parse_mode="HTML"
        )


async def get_user_current_menu(user_id: int) -> Optional[str]:
    """Get user's current menu from session"""
    session = await db.get_user_session(user_id)
    if session:
        return session.current_menu_id
    return None


def clear_menu_cache(menu_id: Optional[str] = None):
    """Clear menu cache (called when admin edits menus)"""
    global _menu_cache
    if menu_id:
        _menu_cache.pop(menu_id, None)
    else:
        _menu_cache.clear()
