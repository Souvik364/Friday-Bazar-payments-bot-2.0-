import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import asyncio

from utils.translations import get_text, get_language_keyboard, TRANSLATIONS

logger = logging.getLogger(__name__)
language_router = Router()


async def get_user_language(state: FSMContext) -> str:
    """Get user's selected language from state, default to English."""
    data = await state.get_data()
    return data.get('language', 'en')


async def set_user_language(state: FSMContext, lang: str):
    """Set user's preferred language in state."""
    await state.update_data(language=lang)


@language_router.callback_query(F.data.startswith("lang_"))
async def handle_language_selection(callback: CallbackQuery, state: FSMContext):
    """Handle language selection callback."""
    lang_code = callback.data.split("_")[1]
    
    if lang_code not in TRANSLATIONS:
        lang_code = "en"
    
    await set_user_language(state, lang_code)
    await callback.answer(f"✅ Language changed to {TRANSLATIONS[lang_code]['language_name']}")
    
    lang_name = TRANSLATIONS[lang_code]['language_name']
    await callback.message.answer(
        get_text(lang_code, "language_changed"),
        parse_mode="HTML"
    )
    
    from handlers.start import get_main_menu_keyboard
    
    welcome_text = get_text(lang_code, "welcome", callback.from_user.first_name)
    await callback.message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(lang_code)
    )


@language_router.message(F.text.in_(["🌐 Change Language", "🌐 ভাষা পরিবর্তন", "🌐 भाषा बदलें"]))
async def cmd_change_language(message: Message, state: FSMContext):
    """Handle change language button."""
    lang = await get_user_language(state)
    
    await message.answer(
        get_text(lang, "select_language"),
        parse_mode="HTML",
        reply_markup=get_language_keyboard()
    )
