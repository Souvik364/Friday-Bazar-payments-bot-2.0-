"""
Friday Bazar Payments - Admin Price & Service Management
======================================================
Manage dynamic pricing, service availability, and plan-specific QRs.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from src.utils.admin_utils import admin_only, log_admin_action
from src.services.settings import settings_manager

router = Router()

class PriceStates(StatesGroup):
    waiting_for_amount = State() # For single edit
    waiting_for_percentage = State() # For bulk update
    waiting_for_plan_qr = State() # For plan QR upload

@router.callback_query(F.data == "admin_price_menu")
@admin_only
async def price_menu(callback: CallbackQuery):
    """Show Price Management Menu"""
    text = (
        "━━━━━━━━━━━━━━━━━\n"
        "💰 **Service Management**\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "Manage prices, availability, and QRs.\n\n"
        "Choose an option:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Edit Services / Plans", callback_data="admin_price_edit_list")],
        [InlineKeyboardButton(text="📦 Bulk Price Update", callback_data="admin_price_bulk")],
        [InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_dashboard")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# --- Service List ---
@router.callback_query(F.data == "admin_price_edit_list")
@admin_only
async def edit_list(callback: CallbackQuery):
    """Show list of services to edit"""
    services = settings_manager.get_all_services()
    
    builder = []
    
    for sid, sdata in services.items():
        # Status icon
        status = "🟢" if sdata.get("available", True) else "🔴"
        
        builder.append([InlineKeyboardButton(
            text=f"{status} {sdata['emoji']} {sdata['name']}", 
            callback_data=f"admin_edit_service:{sid}"
        )])
        
    builder.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin_price_menu")])
    
    await callback.message.edit_text(
        "📦 **Select Service to Edit:**\n"
        "🟢 = Active | 🔴 = Disabled",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=builder),
        parse_mode="Markdown"
    )

# --- Edit Service Menu ---
@router.callback_query(F.data.startswith("admin_edit_service:"))
async def edit_specific_service(callback: CallbackQuery, state: FSMContext):
    service_id = callback.data.split(":")[1]
    service = settings_manager.get_service(service_id)
    
    if not service:
        await callback.answer("Service not found!", show_alert=True)
        return

    is_active = service.get("available", True)
    status_text = "🟢 Active" if is_active else "🔴 Disabled"
    
    text = (
        f"📝 **Edit: {service['name']}**\n"
        f"Status: {status_text}\n\n"
        "Select an action:"
    )
    
    # Toggle Button
    toggle_action = "disable" if is_active else "enable"
    toggle_text = "🔴 Disable Service" if is_active else "✅ Enable Service"
    
    rows = []
    
    # Toggle Availability
    rows.append([InlineKeyboardButton(text=toggle_text, callback_data=f"admin_svc_toggle:{service_id}:{toggle_action}")])
    
    # Plans
    rows.append([InlineKeyboardButton(text="👇 -- Manage Plans -- 👇", callback_data="noop")])
    
    for idx, plan in enumerate(service['plans']):
        rows.append([InlineKeyboardButton(
            text=f"⚙️ {plan['duration']} (₹{plan['price']})",
            callback_data=f"admin_plan_menu:{service_id}:{idx}"
        )])
        
    rows.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin_price_edit_list")])
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="Markdown")

# --- Toggle Service ---
@router.callback_query(F.data.startswith("admin_svc_toggle:"))
async def toggle_service(callback: CallbackQuery):
    parts = callback.data.split(":")
    service_id = parts[1]
    action = parts[2]
    
    new_status = (action == "enable")
    
    await settings_manager.update_service(service_id, {"available": new_status})
    await log_admin_action(callback.from_user.id, "Admin", "service_toggle", {"service": service_id, "enabled": new_status})
    
    await callback.answer(f"Service {'Enabled' if new_status else 'Disabled'}!")
    
    # Refresh menu
    # Hack: Reset callback data to show service menu again
    callback.data = f"admin_edit_service:{service_id}"
    await edit_specific_service(callback, None)


# --- Plan Menu ---
@router.callback_query(F.data.startswith("admin_plan_menu:"))
async def plan_menu(callback: CallbackQuery):
    parts = callback.data.split(":")
    service_id = parts[1]
    plan_idx = int(parts[2])
    
    service = settings_manager.get_service(service_id)
    plan = service['plans'][plan_idx]
    
    has_qr = bool(plan.get("custom_qr_file_id"))
    qr_status = "✅ Custom QR Set" if has_qr else "🌐 Default/Dynamic"
    
    text = (
        f"⚙️ **Manage Plan: {service['name']} - {plan['duration']}**\n\n"
        f"💰 Price: ₹{plan['price']}\n"
        f"🖼️ QR Mode: {qr_status}\n"
    )
    
    rows = [
        [InlineKeyboardButton(text="💰 Change Price", callback_data=f"admin_edit_plan_price:{service_id}:{plan_idx}")],
        [InlineKeyboardButton(text="🖼️ Set Custom QR", callback_data=f"admin_set_plan_qr:{service_id}:{plan_idx}")],
    ]
    
    if has_qr:
         rows.append([InlineKeyboardButton(text="🗑️ Remove Custom QR", callback_data=f"admin_del_plan_qr:{service_id}:{plan_idx}")])
         
    rows.append([InlineKeyboardButton(text="🔙 Back", callback_data=f"admin_edit_service:{service_id}")])
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="Markdown")

# --- Change Price ---
@router.callback_query(F.data.startswith("admin_edit_plan_price:"))
async def ask_price(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    service_id = parts[1]
    plan_idx = int(parts[2])
    
    service = settings_manager.get_service(service_id)
    plan = service['plans'][plan_idx]
    
    await state.update_data(service_id=service_id, plan_idx=plan_idx, old_price=plan['price'])
    await state.set_state(PriceStates.waiting_for_amount)
    
    await callback.message.answer(
        f"📝 **Edit Price for {service['name']} {plan['duration']}**\n\n"
        f"Current: ₹{plan['price']}\n"
        "👉 Enter new price:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_price_menu")]])
    )
    await callback.answer()

@router.message(PriceStates.waiting_for_amount)
async def receive_price(message: Message, state: FSMContext):
    try:
        new_price = int(message.text.strip())
    except:
        await message.answer("❌ Invalid number.")
        return
        
    data = await state.get_data()
    service_id = data['service_id']
    plan_idx = data['plan_idx']
    
    service = settings_manager.get_service(service_id)
    service['plans'][plan_idx]['price'] = new_price
    
    await settings_manager.update_service(service_id, {"plans": service['plans']})
    
    await message.answer(f"✅ Price updated to ₹{new_price}")
    await state.clear()
    
    # Optional: Send simple text with button to go back
    await message.answer("Use menu to continue:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data=f"admin_plan_menu:{service_id}:{plan_idx}")]
    ]))

# --- Set Plan QR ---
@router.callback_query(F.data.startswith("admin_set_plan_qr:"))
async def ask_plan_qr(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    service_id = parts[1]
    plan_idx = int(parts[2])
    
    await state.update_data(service_id=service_id, plan_idx=plan_idx)
    await state.set_state(PriceStates.waiting_for_plan_qr)
    
    await callback.message.answer(
        "📸 **Upload Custom QR for Plan**\n\n"
        "Send the QR code image you want to use specifically for this plan.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="admin_price_menu")]])
    )
    await callback.answer()

@router.message(PriceStates.waiting_for_plan_qr, F.photo)
async def receive_plan_qr(message: Message, state: FSMContext):
    data = await state.get_data()
    service_id = data['service_id']
    plan_idx = data['plan_idx']
    
    photo = message.photo[-1].file_id
    
    service = settings_manager.get_service(service_id)
    service['plans'][plan_idx]['custom_qr_file_id'] = photo
    
    await settings_manager.update_service(service_id, {"plans": service['plans']})
    
    await message.answer("✅ **Custom Plan QR Set!**")
    await state.clear()
    
    await message.answer("Use menu to continue:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data=f"admin_plan_menu:{service_id}:{plan_idx}")]
    ]))

# --- Delete Plan QR ---
@router.callback_query(F.data.startswith("admin_del_plan_qr:"))
async def delete_plan_qr(callback: CallbackQuery):
    parts = callback.data.split(":")
    service_id = parts[1]
    plan_idx = int(parts[2])
    
    service = settings_manager.get_service(service_id)
    if "custom_qr_file_id" in service['plans'][plan_idx]:
        del service['plans'][plan_idx]['custom_qr_file_id']
        await settings_manager.update_service(service_id, {"plans": service['plans']})
        await callback.answer("✅ QR Removed")
    
    # Refresh
    callback.data = f"admin_plan_menu:{service_id}:{plan_idx}"
    await plan_menu(callback)


# --- Bulk Update ---
@router.callback_query(F.data == "admin_price_bulk")
async def bulk_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📦 **Bulk Price Update**\n\n"
        "Choose update method:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📈 Increase by %", callback_data="admin_bulk:inc")],
            [InlineKeyboardButton(text="📉 Decrease by %", callback_data="admin_bulk:dec")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="admin_price_menu")]
        ]),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("admin_bulk:"))
async def ask_bulk_percent(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.split(":")[1]
    await state.update_data(bulk_mode=mode)
    await state.set_state(PriceStates.waiting_for_percentage)
    
    action = "increase" if mode == "inc" else "decrease"
    
    await callback.message.answer(
        f"📈 **Bulk {action.title()}**\n\n"
        f"Enter percentage to {action} (1-100):"
    )
    await callback.answer()

@router.message(PriceStates.waiting_for_percentage)
async def receive_bulk_percent(message: Message, state: FSMContext):
    try:
        percent = float(message.text.strip())
        if not (0 < percent <= 100): raise ValueError
    except:
        await message.answer("❌ Invalid percentage. Enter 1-100.")
        return
        
    data = await state.get_data()
    is_increase = data['bulk_mode'] == "inc"
    
    count = await settings_manager.bulk_update_prices(percent, increase=is_increase)
    
    await log_admin_action(
        message.from_user.id, "Admin", "bulk_price_update",
        {"percent": percent, "increase": is_increase, "count": count}
    )
    
    await message.answer(f"✅ **Bulk Update Complete!**\n\nUpdated {count} services successfully.")
    await state.clear()
