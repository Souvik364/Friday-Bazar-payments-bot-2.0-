import logging
import asyncio
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.filters import Command
from aiogram.enums import ChatAction, ContentType

from config import ADMIN_ID
from utils.translations import get_text
from handlers.language import get_user_language

logger = logging.getLogger(__name__)
admin_router = Router()

@admin_router.message(Command("admin"))
async def admin_dashboard(message: Message):
    """Show admin dashboard (admin only)."""
    if message.from_user.id != ADMIN_ID:
        return
    
    await message.answer(
        "👨‍💼 <b>ADMIN DASHBOARD</b>\n\n"
        "🎛️ <b>Available Commands:</b>\n\n"
        "📊 /stats - View statistics\n"
        "👥 /users - User management\n"
        "💳 /pending - View pending payments\n"
        "📢 /broadcast - Send message to all users\n\n"
        "💡 <i>Manage your bot efficiently!</i>",
        parse_mode="HTML"
    )

@admin_router.callback_query(F.data.startswith("contact_"))
async def contact_user(callback: CallbackQuery, bot: Bot):
    """Allow admin to contact user directly."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Unauthorized!", show_alert=True)
        return
    
    user_id_str = callback.data.split("_", 1)[1]
    
    try:
        user_id = int(user_id_str)
        await callback.answer("📞 Opening chat...")
        
        await callback.message.answer(
            f"📞 <b>Contact User</b>\n\n"
            f"User ID: <code>{user_id}</code>\n\n"
            f"Click to message: <a href='tg://user?id={user_id}'>Message User</a>",
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.answer("❌ Error", show_alert=True)
        logger.error(f"Error in contact_user: {e}")

@admin_router.callback_query(F.data.startswith("approve_") | F.data.startswith("reject_"))
async def handle_admin_decision(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Handle admin approval or rejection with SAFE message editing."""
    
    # 1. Security Check
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Unauthorized access!", show_alert=True)
        return
    
    # 2. Parse Data
    try:
        action, user_id_str = callback.data.split("_", 1)
        user_id = int(user_id_str)
    except ValueError:
        await callback.answer("❌ Invalid data", show_alert=True)
        return
    
    # 3. Get User Language (Safe Method)
    try:
        user_storage_key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
        user_state = FSMContext(bot=bot, storage=state.storage, key=user_storage_key)
        lang = await get_user_language(user_state)
    except Exception as e:
        logger.error(f"Could not fetch user language: {e}")
        lang = "en"  # Fallback to English if state fetch fails
    
    await bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    try:
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Prepare status text based on action
        if action == "approve":
            status_text = f"✅ <b>APPROVED</b>\nBy: Admin\nTime: {current_time}"
            user_msg_key = "approved"
            log_msg = f"✅ Approved User {user_id}"
        else:
            status_text = f"❌ <b>REJECTED</b>\nBy: Admin\nTime: {current_time}"
            user_msg_key = "rejected"
            log_msg = f"❌ Rejected User {user_id}"

        # 4. Notify the User (Try/Except in case user blocked bot)
        try:
            await bot.send_message(
                chat_id=user_id,
                text=get_text(lang, user_msg_key),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Could not message user {user_id}: {e}")
            # We continue execution even if we can't message the user

        # 5. FIX: Edit Admin Message (Handles both Text and Photo/Caption)
        # Check if the original message has a caption (is a Photo/Document)
        if callback.message.caption:
            await callback.message.edit_caption(
                caption=f"{callback.message.caption}\n\n{status_text}",
                parse_mode="HTML",
                reply_markup=None
            )
        # Otherwise, assume it is a Text message
        elif callback.message.text:
            await callback.message.edit_text(
                text=f"{callback.message.text}\n\n{status_text}",
                parse_mode="HTML",
                reply_markup=None
            )
        else:
            # Fallback if message type is weird
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer(status_text, parse_mode="HTML")

        # 6. Finalize
        await bot.send_message(ADMIN_ID, log_msg)
        await user_state.clear()
        await user_state.update_data(language=lang)
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR in admin decision: {e}", exc_info=True)
        await callback.answer(f"❌ Error: {str(e)[:50]}...", show_alert=True)
        
