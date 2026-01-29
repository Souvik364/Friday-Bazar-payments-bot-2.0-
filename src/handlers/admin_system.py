"""
Friday Bazar Payments - Admin System Control
=============================================
Toggle payment system and maintenance mode
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from src.utils.admin_utils import admin_only, log_admin_action
from src.services.settings import settings_manager

router = Router()

class SystemStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_reason = State()

@router.callback_query(F.data == "admin_payment_toggle")
@admin_only
async def payment_control_menu(callback: CallbackQuery):
    """Show Payment Control Menu"""
    is_enabled = settings_manager.is_payment_enabled()
    disabled_msg = settings_manager.get_disabled_message()
    
    status = "✅ ACTIVE" if is_enabled else "🔴 DISABLED"
    status_desc = "Accepting orders" if is_enabled else "Maintenance Mode"
    
    text = (
        "🔧 **Payment System Control**\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"Current Status: {status}\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        f"{status_desc}\n\n"
        f"**Maintenance Message:**\n"
        f"`{disabled_msg}`"
    )
    
    btn_text = "🔴 Disable Payments" if is_enabled else "✅ Enable Payments"
    callback_action = "admin_sys_disable" if is_enabled else "admin_sys_enable"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_text, callback_data=callback_action)],
        [InlineKeyboardButton(text="📝 Set Maintenance Message", callback_data="admin_sys_msg")],
        [InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_dashboard")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# --- Disable ---
@router.callback_query(F.data == "admin_sys_disable")
async def disable_ask_reason(callback: CallbackQuery):
    """Ask reason for disabling"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1️⃣ Maintenance", callback_data="admin_reason:Maintenance")],
        [InlineKeyboardButton(text="2️⃣ Payment Issues", callback_data="admin_reason:Payment Gateway Issue")],
        [InlineKeyboardButton(text="3️⃣ Out of Stock", callback_data="admin_reason:Stock Out")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="admin_payment_toggle")]
    ])
    
    await callback.message.edit_text(
        "⚠️ **Disable Payment System**\n\nSelect a reason:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("admin_reason:"))
async def confirm_disable(callback: CallbackQuery):
    reason = callback.data.split(":")[1]
    
    updates = {
        "enabled": False,
        "disabled_at": datetime.now().isoformat(),
        "disabled_by": callback.from_user.id,
        "disabled_reason": reason
    }
    
    await settings_manager.update_settings({"payment_system": updates})
    
    await log_admin_action(callback.from_user.id, "Admin", "system_disable", {"reason": reason})
    
    await callback.message.edit_text(
        f"✅ **System Disabled**\n\nReason: {reason}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back", callback_data="admin_payment_toggle")]
        ]),
        parse_mode="Markdown"
    )

# --- Enable ---
@router.callback_query(F.data == "admin_sys_enable")
async def enable_system(callback: CallbackQuery):
    updates = {
        "enabled": True,
        "disabled_at": None
    }
    
    await settings_manager.update_settings({"payment_system": updates})
    await log_admin_action(callback.from_user.id, "Admin", "system_enable", {})
    
    await callback.answer("✅ System Enabled!")
    await payment_control_menu(callback)

# --- Set Message ---
@router.callback_query(F.data == "admin_sys_msg")
async def ask_message(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SystemStates.waiting_for_message)
    await callback.message.answer(
        "📝 **Set Maintenance Message**\n\n"
        "Enter the message users will see when payments are disabled:"
    )
    await callback.answer()

@router.message(SystemStates.waiting_for_message)
async def set_message(message: Message, state: FSMContext):
    msg = message.text.strip()
    
    updates = {"disabled_message": msg}
    await settings_manager.update_settings({"payment_system": updates})
    
    await message.answer("✅ **Message Saved!**\n\n" + msg)
    await state.clear()
