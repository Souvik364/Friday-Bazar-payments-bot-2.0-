"""
Friday Bazar Payments - Admin QR Management
============================================
Manage default UPI QR codes and Dynamic UPI Configuration
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from src.utils.admin_utils import admin_only, log_admin_action
from src.services.settings import settings_manager
from src.config import UPI_ID as CONFIG_UPI_ID, UPI_NAME as CONFIG_UPI_NAME

router = Router()

class QRStates(StatesGroup):
    waiting_for_qr = State()
    waiting_for_upi_id = State()
    waiting_for_upi_name = State()

@router.callback_query(F.data == "admin_qr_menu")
@admin_only
async def qr_menu(callback: CallbackQuery):
    """Show QR Management Menu"""
    await _show_qr_menu(callback.message, is_edit=True)

async def _show_qr_menu(message, is_edit=False):
    qr_settings = settings_manager.get_qr_settings()
    is_default = qr_settings.get("use_default_qr", False)
    
    status = "✅ Active (Default QR)" if is_default else "🔄 Dynamic Generation"
    updated_at = qr_settings.get("updated_at", "N/A")
    if updated_at and updated_at != "N/A":
        try:
            dt = datetime.fromisoformat(updated_at)
            updated_at = dt.strftime('%b %d, %Y, %I:%M %p')
        except:
            pass
            
    text = (
        "━━━━━━━━━━━━━━━━━\n"
        "🖼️ **QR Code Settings**\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        f"Status: {status}\n"
        f"Last Updated: {updated_at}\n\n"
        "**Options:**\n"
        "1. **Default QR**: Upload a scan-only QR for ALL payments.\n"
        "2. **Dynamic UPI**: Configure UPI ID for generated QRs."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Upload Default QR", callback_data="admin_set_qr")],
        [InlineKeyboardButton(text="👁️ View Current QR", callback_data="admin_view_qr")],
        [InlineKeyboardButton(text="⚙️ Configure UPI Details", callback_data="admin_upi_config")],
        [InlineKeyboardButton(text="🗑️ Delete Default QR", callback_data="admin_delete_qr")] if is_default else [],
        [InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_dashboard")]
    ])
    
    if is_edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


# --- Set QR ---
@router.message(Command("setqr"))
@router.callback_query(F.data == "admin_set_qr")
@admin_only
async def start_set_qr(event, state: FSMContext):
    """Start QR upload flow"""
    msg = event.message if isinstance(event, CallbackQuery) else event
    
    await msg.answer(
        "📸 **Upload Default QR Code**\n\n"
        "Please send the QR code image that will be used for all payments.\n\n"
        "💡 *Tip: Make sure the QR code is clear and scannable*",
        parse_mode="Markdown"
    )
    await state.set_state(QRStates.waiting_for_qr)
    
    if isinstance(event, CallbackQuery):
        await event.answer()

@router.message(QRStates.waiting_for_qr, F.photo)
async def receive_qr(message: Message, state: FSMContext):
    """Receive and save QR"""
    if not await settings_manager.is_payment_enabled(): 
        pass

    photo = message.photo[-1]
    file_id = photo.file_id
    
    # Save settings
    updates = {
        "use_default_qr": True,
        "default_qr_file_id": file_id,
        "updated_by": message.from_user.id,
        "updated_at": datetime.now().isoformat()
    }
    
    await settings_manager.update_settings({"qr_settings": updates})
    
    # Log
    await log_admin_action(
        message.from_user.id, 
        message.from_user.username or "Admin",
        "update_qr",
        {"file_id": file_id}
    )
    
    await message.answer(
        "✅ **Default QR Code Saved Successfully!**\n\n"
        "This QR will now be used for ALL payments."
    )
    await state.clear()
    
    # Show menu again
    await _show_qr_menu(message)

# --- View QR ---
@router.message(Command("viewqr"))
@router.callback_query(F.data == "admin_view_qr")
@admin_only
async def view_qr(event):
    """View current QR"""
    qr_settings = settings_manager.get_qr_settings()
    is_default = qr_settings.get("use_default_qr", False)
    file_id = qr_settings.get("default_qr_file_id")
    
    msg = event.message if isinstance(event, CallbackQuery) else event
    
    if is_default and file_id:
        await msg.answer_photo(
            file_id,
            caption="🖼️ **Current Default QR Code**\n\nUsed for all payments.",
            parse_mode="Markdown"
        )
    else:
        await msg.answer("ℹ️ **Dynamic QR Mode Active**\n\nNo default QR is currently set. System is generating unique QRs for each order.")
        
    if isinstance(event, CallbackQuery):
        await event.answer()
    
    # Send menu below to not block
    await _show_qr_menu(msg)

# --- Delete QR ---
@router.message(Command("deleteqr"))
@router.callback_query(F.data == "admin_delete_qr")
@admin_only
async def delete_qr(event):
    """Delete default QR"""
    qr_settings = settings_manager.get_qr_settings()
    if not qr_settings.get("use_default_qr", False):
        if isinstance(event, CallbackQuery):
            await event.answer("Already in dynamic mode!", show_alert=True)
        return

    # Delete
    empty_qr = {
        "use_default_qr": False,
        "default_qr_file_id": None,
        "updated_by": event.from_user.id,
        "updated_at": datetime.now().isoformat()
    }
    await settings_manager.update_settings({"qr_settings": empty_qr})
    
    msg = event.message if isinstance(event, CallbackQuery) else event
    await msg.answer("✅ **Default QR Deleted!**\n\nReverted to Dynamic QR generation.")
    
    if isinstance(event, CallbackQuery):
        await event.answer()
    
    await _show_qr_menu(msg)


# =========================================================
#                   UPI CONFIGURATION
# =========================================================

@router.callback_query(F.data == "admin_upi_config")
async def upi_config_menu(callback: CallbackQuery):
    """Show UPI Config Menu"""
    qr_settings = settings_manager.get_qr_settings()
    
    current_upi = qr_settings.get("upi_id") or CONFIG_UPI_ID
    current_name = qr_settings.get("upi_name") or CONFIG_UPI_NAME
    
    text = (
        "⚙️ **Configure UPI Details**\n\n"
        "These details are used when **Dynamic QR** generation is active.\n"
        "Changing this will instantly update the QR codes generated for new orders.\n\n"
        f"🆔 **vPA / UPI ID:** `{current_upi}`\n"
        f"👤 **Payee Name:** `{current_name}`"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Edit UPI ID", callback_data="admin_edit_upi_id")],
        [InlineKeyboardButton(text="✏️ Edit Payee Name", callback_data="admin_edit_upi_name")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="admin_qr_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# -- Edit UPI ID --
@router.callback_query(F.data == "admin_edit_upi_id")
async def ask_upi_id(callback: CallbackQuery, state: FSMContext):
    await state.set_state(QRStates.waiting_for_upi_id)
    await callback.message.answer(
        "🆔 **Enter New UPI ID**\n\n"
        "Please enter the valid VPA (e.g., `business@paytm`).\n"
        "Type `cancel` to abort."
    )
    await callback.answer()

@router.message(QRStates.waiting_for_upi_id)
async def receive_upi_id(message: Message, state: FSMContext):
    if message.text.lower() == "cancel":
        await state.clear()
        await message.answer("Cancelled.")
        await _show_qr_menu(message)
        return

    new_upi = message.text.strip()
    if "@" not in new_upi: # Basic validation
        await message.answer("❌ Invalid UPI ID format. It should contain '@'. Try again.")
        return

    await settings_manager.update_settings({"qr_settings": {"upi_id": new_upi}})
    await log_admin_action(message.from_user.id, "Admin", "upi_change", {"new_upi": new_upi})
    
    await message.answer(f"✅ UPI ID updated to `{new_upi}`")
    await state.clear()
    
    # Return to config menu
    # For now, just show main QR menu or call config menu again via message
    # To properly return to the message flow, we'll just show the QR menu
    await _show_qr_menu(message)


# -- Edit UPI Name --
@router.callback_query(F.data == "admin_edit_upi_name")
async def ask_upi_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(QRStates.waiting_for_upi_name)
    await callback.message.answer(
        "👤 **Enter Payee Name**\n\n"
        "This name will appear when scanning the QR.\n"
        "Type `cancel` to abort."
    )
    await callback.answer()

@router.message(QRStates.waiting_for_upi_name)
async def receive_upi_name(message: Message, state: FSMContext):
    if message.text.lower() == "cancel":
        await state.clear()
        await message.answer("Cancelled.")
        await _show_qr_menu(message)
        return

    new_name = message.text.strip()
    
    await settings_manager.update_settings({"qr_settings": {"upi_name": new_name}})
    await log_admin_action(message.from_user.id, "Admin", "upi_name_change", {"new_name": new_name})
    
    await message.answer(f"✅ Payee Name updated to `{new_name}`")
    await state.clear()
    await _show_qr_menu(message)
