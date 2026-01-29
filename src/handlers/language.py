"""
Friday Bazar Payments - Language Selection Handler
===================================================
Handles language selection and changes
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.services.db import db
from src.data.translations import get_text

router = Router()

# FSM States
class LanguageStates(StatesGroup):
    selecting = State()


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Generate language selection keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
        InlineKeyboardButton(text="🇮🇳 हिंदी", callback_data="lang:hi")
    )
    builder.row(
        InlineKeyboardButton(text="🇧🇩 বাংলা", callback_data="lang:bn")
    )
    return builder.as_markup()


@router.message(Command("language"))
async def cmd_language(message: Message, state: FSMContext):
    """Change language command"""
    await message.answer(
        get_text("select_language", "en"),  # Show in all languages
        reply_markup=get_language_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(LanguageStates.selecting)


@router.callback_query(F.data.startswith("lang:"))
async def select_language(callback: CallbackQuery, state: FSMContext, lang: str = None, t=None):
    """Handle language selection"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    # Get selected language from callback
    new_lang = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    # Update user language in database
    await db.update_user(user_id, {"language": new_lang})
    
    # Get confirmation message in the NEW language
    confirmation = get_text("language_changed", new_lang)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    
    await callback.message.edit_text(
        confirmation,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer("✅")
    
    await state.clear()
