
import asyncio
import logging
import re
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.enums import ChatAction

from handlers import PremiumStates
from utils.qr_generator import generate_payment_qr
from utils.timer import start_payment_timer
from utils.translations import get_text
from handlers.language import get_user_language
from config import ADMIN_ID

logger = logging.getLogger(__name__)
premium_router = Router()


def get_plan_selection_keyboard(lang="en") -> InlineKeyboardMarkup:
    """Create inline keyboard with plan options."""
    # Note: Plan names could also be translated if desired
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 Month - ₹20", callback_data="plan_1month_20")],
            [InlineKeyboardButton(text="3 Months - ₹55", callback_data="plan_3months_55")],
            [InlineKeyboardButton(text=get_text(lang, "coming_soon") + " - ₹100", callback_data="coming_soon")],
            [InlineKeyboardButton(text=get_text(lang, "back_menu"), callback_data="back_to_menu")]
        ]
    )
    return keyboard


def get_payment_actions_keyboard(lang="en") -> InlineKeyboardMarkup:
    """Create keyboard for actions during payment."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "upload_now"), callback_data="upload_now")],
            [InlineKeyboardButton(text=get_text(lang, "cancel_payment"), callback_data="cancel_payment")]
        ]
    )
    return keyboard


def get_admin_approval_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Create admin approval keyboard with user ID embedded."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{user_id}")
            ],
            [InlineKeyboardButton(text="📞 Contact User", callback_data=f"contact_{user_id}")]
        ]
    )
    return keyboard


def is_valid_email(email: str) -> bool:
    """Check if email format is valid."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None


@premium_router.message(F.text == "🎥 YouTube Premium")
async def show_premium_plans(message: Message, state: FSMContext, bot: Bot):
    """Show YouTube Premium plan options with animation."""
    lang = await get_user_language(state)
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    await asyncio.sleep(0.5)
    
    await state.set_state(PremiumStates.waiting_for_plan_selection)
    
    await message.answer(
        "✨ <b>Loading...</b>",
        parse_mode="HTML"
    )
    await asyncio.sleep(0.3)
    
    await message.answer(
        get_text(lang, "choose_plan"),
        parse_mode="HTML",
        reply_markup=get_plan_selection_keyboard(lang)
    )


@premium_router.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Return to main menu."""
    lang = await get_user_language(state)
    await callback.answer(get_text(lang, "back_menu"))
    await state.clear()
    await state.update_data(language=lang) # Preserve language
    
    from handlers.start import get_main_menu_keyboard
    
    await callback.message.answer(
        "🏠",
        reply_markup=get_main_menu_keyboard(lang)
    )


@premium_router.callback_query(F.data == "coming_soon")
async def handle_coming_soon(callback: CallbackQuery, state: FSMContext):
    """Handle coming soon plan click."""
    lang = await get_user_language(state)
    await callback.answer(
        get_text(lang, "coming_soon"),
        show_alert=True
    )


@premium_router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    """Cancel payment and return to plans."""
    lang = await get_user_language(state)
    await callback.answer("❌ Cancelled")
    await state.set_state(PremiumStates.waiting_for_plan_selection)
    
    await callback.message.answer(
        get_text(lang, "choose_plan"),
        parse_mode="HTML",
        reply_markup=get_plan_selection_keyboard(lang)
    )


@premium_router.callback_query(F.data.startswith("plan_"))
async def process_plan_selection(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle plan selection and show QR code with flexible upload."""
    lang = await get_user_language(state)
    await callback.answer("⏳ Processing...")
    
    await bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_PHOTO)
    await asyncio.sleep(0.5)
    
    callback_data = callback.data
    
    plan_mapping = {
        "plan_1month_20": ("1 Month YouTube Premium", 20),
        "plan_3months_55": ("3 Months YouTube Premium", 55)
    }
    
    if callback_data not in plan_mapping:
        await callback.message.answer("❌ Invalid plan selected.")
        return
    
    plan_name, amount = plan_mapping[callback_data]
    
    timer_end_time = datetime.now() + timedelta(minutes=5)
    
    await state.update_data(
        plan_name=plan_name,
        amount=amount,
        timer_end=timer_end_time.isoformat()
    )
    await state.set_state(PremiumStates.viewing_qr)
    
    qr_buffer = generate_payment_qr(plan_name, amount)
    qr_photo = BufferedInputFile(qr_buffer.read(), filename="payment_qr.png")
    
    timer_text = timer_end_time.strftime('%I:%M %p')
    caption_text = get_text(lang, "payment_details", plan_name, amount, timer_text)
    
    await callback.message.answer_photo(
        photo=qr_photo,
        caption=caption_text,
        parse_mode="HTML",
        reply_markup=get_payment_actions_keyboard(lang)
    )
    
    await state.set_state(PremiumStates.timer_running)
    
    await callback.message.answer(
        get_text(lang, "timer_started"),
        parse_mode="HTML"
    )
    
    asyncio.create_task(
        start_payment_timer(bot, callback.message.chat.id, state, duration=300)
    )
    
    logger.info(f"User {callback.from_user.id} selected plan: {plan_name} (₹{amount})")


@premium_router.callback_query(F.data == "upload_now")
async def prompt_upload(callback: CallbackQuery, state: FSMContext):
    """Prompt user to upload screenshot."""
    lang = await get_user_language(state)
    await callback.answer("📸")
    
    await callback.message.answer(
        "📸 <b>Upload Payment Screenshot</b>",
        parse_mode="HTML"
    )


@premium_router.message(
    StateFilter(PremiumStates.timer_running, PremiumStates.waiting_for_screenshot),
    F.photo
)
async def handle_payment_screenshot(message: Message, state: FSMContext, bot: Bot):
    """Handle payment screenshot submission and Ask for Email."""
    lang = await get_user_language(state)
    user_data = await state.get_data()
    timer_end = user_data.get('timer_end')
    
    # Check timer (optional strictness)
    if timer_end:
        timer_end_dt = datetime.fromisoformat(timer_end)
        if datetime.now() > timer_end_dt:
            # We can be lenient here and still accept if it's close, 
            # but let's stick to the logic: if time up, fail.
            # OR better UX: Allow it if they are already uploading.
            pass 
    
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    await asyncio.sleep(0.3)
    
    photo = message.photo[-1]
    photo_file_id = photo.file_id
    
    # SAVE PHOTO and Ask for Email
    await state.update_data(screenshot_file_id=photo_file_id)
    await state.set_state(PremiumStates.waiting_for_email)
    
    await message.answer(
        get_text(lang, "screenshot_received"),
        parse_mode="HTML"
    )


@premium_router.message(StateFilter(PremiumStates.waiting_for_email), F.text)
async def handle_email_submission(message: Message, state: FSMContext, bot: Bot):
    """Handle Email ID submission and Send to Admin."""
    lang = await get_user_language(state)
    email = message.text.strip()
    
    if not is_valid_email(email):
        await message.answer(
            get_text(lang, "invalid_email"),
            parse_mode="HTML"
        )
        return
        
    # Valid Email - Proceed to notify Admin
    await state.update_data(email=email)
    await state.set_state(PremiumStates.pending_approval)
    
    user_data = await state.get_data()
    plan_name = user_data.get("plan_name", "Unknown")
    amount = user_data.get("amount", 0)
    photo_file_id = user_data.get("screenshot_file_id")
    
    user_id = message.from_user.id
    username = message.from_user.username or "No username"
    full_name = message.from_user.full_name or "User"
    
    # Admin Notification
    admin_message = (
        f"🔔 <b>NEW PREMIUM REQUEST</b> 🔔\n\n"
        f"👤 <b>USER DETAILS</b>\n"
        f"📛 Name: {full_name}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 User: @{username}\n\n"
        f"💎 <b>ORDER DETAILS</b>\n"
        f"📦 Plan: <b>{plan_name}</b>\n"
        f"💰 Paid: <b>₹{amount}</b>\n"
        f"📧 Email: <b>{email}</b>\n"
        f"📅 Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n\n"
        f"👇 <i>Review screenshot & Approve</i>"
    )
    
    try:
        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file_id,
            caption=admin_message,
            parse_mode="HTML",
            reply_markup=get_admin_approval_keyboard(user_id)
        )
        
        # User Notification
        await message.answer(
            get_text(lang, "submission_complete", email),
            parse_mode="HTML"
        )
        
        logger.info(f"Premium request sent to admin for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}", exc_info=True)
        await message.answer("⚠️ Error processing request. Please contact support.")


@premium_router.message(StateFilter(PremiumStates.timer_running, PremiumStates.waiting_for_screenshot))
async def handle_non_photo_during_payment(message: Message):
    """Handle non-photo messages during payment process."""
    await message.answer("⚠️ Please send the payment screenshot as a PHOTO.")


@premium_router.message(F.photo)
async def handle_unexpected_photo(message: Message, state: FSMContext):
    """Handle photos sent in unexpected states."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("⚠️ Please select a plan first.")
    else:
        # If in waiting_for_email, they might have sent photo again by mistake
        if current_state == PremiumStates.waiting_for_email.state:
             await message.answer("⚠️ We have the screenshot. Please enter your **Email ID**.")
        else:
             await message.answer("⚠️ Unexpected photo. Please follow the instructions.")
    
