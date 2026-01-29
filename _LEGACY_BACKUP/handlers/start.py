from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
import asyncio

# Imports for Language System
from utils.translations import get_text, get_language_keyboard
from handlers.language import get_user_language

start_router = Router()

def get_main_menu_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Create main menu keyboard with translated options."""
    # FIX: Use distinct keys for BUTTONS (e.g., 'btn_help' instead of just 'help')
    # This prevents the button from showing a long help message, 
    # and allows the handler to fetch the correct message text later.
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, "btn_youtube_premium"))],
            [KeyboardButton(text=get_text(lang, "btn_help")), KeyboardButton(text=get_text(lang, "btn_my_status"))],
            [KeyboardButton(text=get_text(lang, "btn_support")), KeyboardButton(text=get_text(lang, "btn_change_language"))]
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an option..."
    )

@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command."""
    lang = await get_user_language(state)
    data = await state.get_data()
    
    if 'language' not in data:
        await message.answer(
            "🌐 <b>Select Your Language</b>\n"
            "अपनी पसंदीदा भाषा चुनें\n"
            "আপনার পছন্দের ভাষা নির্বাচন করুন\n\n"
            "Please choose your preferred language:",
            parse_mode="HTML",
            reply_markup=get_language_keyboard()
        )
        return

    await state.clear()
    await state.update_data(language=lang)
    
    await message.answer("⚡")
    await asyncio.sleep(0.3)
    
    # Use 'msg_welcome' or just 'welcome' for the text body
    welcome_text = get_text(lang, "msg_welcome", message.from_user.first_name)
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(lang)
    )

@start_router.message(Command("help"))
# IMPORTANT: These strings inside F.text.in_([...]) MUST match exactly what 
# get_text(lang, "btn_help") returns in your translation file.
@start_router.message(F.text.in_(["ℹ️ Help", "ℹ️ मदद", "ℹ️ সাহায্য"]))
async def cmd_help(message: Message, state: FSMContext):
    """Show help information."""
    lang = await get_user_language(state)
    
    # FIX: Use a separate key for the actual help CONTENT (e.g., 'msg_help')
    # Do not use the same key as the button, or the bot will just reply "ℹ️ Help"
    help_text = get_text(lang, "msg_help") 
    
    await message.answer(help_text, parse_mode="HTML")

@start_router.message(Command("status"))
@start_router.message(F.text.in_(["📊 My Status", "📊 मेरी स्थिति", "📊 আমার স্ট্যাটাস"]))
async def cmd_status(message: Message, state: FSMContext):
    """Show status."""
    lang = await get_user_language(state)
    
    # FIX: Use a message key for the status header/body
    status_header = get_text(lang, "msg_status_header")
    
    # Mocking status check logic
    await message.answer(f"{status_header}: Active ✅\nUser ID: {message.from_user.id}", parse_mode="HTML")

@start_router.message(Command("support"))
@start_router.message(F.text.in_(["💬 Support", "💬 सहायता", "💬 সাপোর্ট"]))
async def cmd_support(message: Message, state: FSMContext):
    """Show support contact."""
    # Ensure you handle the import safely or define SUPPORT_BOT
    try:
        from config import SUPPORT_BOT
    except ImportError:
        SUPPORT_BOT = "Admin"

    lang = await get_user_language(state)
    
    # Use 'msg_support' for the text body
    support_msg = get_text(lang, "msg_support", SUPPORT_BOT, message.from_user.id)
    await message.answer(support_msg, parse_mode="HTML")

@start_router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    lang = await get_user_language(state)
    await state.clear()
    await message.answer("❌ Cancelled", reply_markup=get_main_menu_keyboard(lang))

