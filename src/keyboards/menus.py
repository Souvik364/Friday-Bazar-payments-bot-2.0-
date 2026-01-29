"""
Friday Bazar Payments - Keyboard Menus
======================================
All keyboard layouts for the bot
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.data.services import get_all_services, get_service_button_text, get_service



def get_main_menu() -> InlineKeyboardMarkup:
    """
    Main menu with inline keyboard buttons matching Friday Bazar Payment Bot design
    """
    # Inline keyboard layout matching the image
    keyboard = [
        [InlineKeyboardButton(text="💸 Start Payment", callback_data="start_payment")],
        [InlineKeyboardButton(text="📱 Telegram Accounts", callback_data="telegram_accounts")],
        [
            InlineKeyboardButton(text="🌑 My Friday Coins", callback_data="action:show_coins"),
            InlineKeyboardButton(text="🔗 Referral Link", callback_data="action:show_referral")
        ],
        [InlineKeyboardButton(text="📜 Terms of Service", callback_data="terms_of_service")],
        [
            InlineKeyboardButton(text="📞 Contact", callback_data="action:show_contact"),
            InlineKeyboardButton(text="🆘 Help", callback_data="action:show_help")
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Cache for service grid
_services_grid_cache = None

def clear_menu_cache():
    """Clear keyboard cache (call when services update)"""
    global _services_grid_cache
    _services_grid_cache = None

def get_services_grid() -> InlineKeyboardMarkup:
    """
    Generate 2-column grid of service buttons
    Cached for performance
    """
    global _services_grid_cache
    if _services_grid_cache:
        return _services_grid_cache

    builder = InlineKeyboardBuilder()
    
    services = list(get_all_services().items())
    
    # Add services in 2-column layout
    for i in range(0, len(services), 2):
        row_buttons = []
        
        # First button in row
        service_id, service_data = services[i]
        is_active = service_data.get('available', True)
        
        if is_active:
            text = f"✨ {service_data['emoji']} {service_data['name']} ✨"
        else:
            text = f"{service_data['emoji']} {service_data['name']} 🔒"

        row_buttons.append(
            InlineKeyboardButton(
                text=text,
                callback_data=f"service:{service_id}"
            )
        )
        
        # Second button in row (if exists)
        if i + 1 < len(services):
            service_id2, service_data2 = services[i + 1]
            is_active2 = service_data2.get('available', True)
            
            if is_active2:
                text2 = f"✨ {service_data2['emoji']} {service_data2['name']} ✨"
            else:
                text2 = f"{service_data2['emoji']} {service_data2['name']} 🔒"

            row_buttons.append(
                InlineKeyboardButton(
                    text=text2,
                    callback_data=f"service:{service_id2}"
                )
            )
        
        builder.row(*row_buttons)
    
    # Add back button
    builder.row(InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_main"))
    
    _services_grid_cache = builder.as_markup()
    return _services_grid_cache

def get_plan_buttons(service_id: str) -> InlineKeyboardMarkup:
    """
    Generate price buttons for a service
    """
    builder = InlineKeyboardBuilder()
    
    builder = InlineKeyboardBuilder()
    
    service = get_service(service_id)
    if not service:
        return builder.as_markup()
    
    for plan in service["plans"]:
        button_text = f"{plan['duration']} - ₹{plan['price']}"
        if plan.get("original_price"):
            button_text += f" (Save ₹{plan['original_price'] - plan['price']})"
        
        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"buy:{service_id}:{plan['duration']}:{plan['price']}"
            )
        )
    
    # Back button
    builder.row(InlineKeyboardButton(text="🔙 Back to Services", callback_data="back_to_services"))
    
    return builder.as_markup()

def get_payment_verification_buttons(order_id: str) -> InlineKeyboardMarkup:
    """
    Buttons for payment verification
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ I've Paid - Upload Screenshot", callback_data=f"upload_proof:{order_id}")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Cancel Order", callback_data=f"cancel_order:{order_id}")
    )
    return builder.as_markup()

def get_admin_approval_buttons(order_id: str) -> InlineKeyboardMarkup:
    """
    Admin approval buttons
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_approve:{order_id}"),
        InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_reject:{order_id}")
    )
    return builder.as_markup()

def get_cancel_button() -> InlineKeyboardMarkup:
    """
    Simple cancel button
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Cancel", callback_data="cancel"))
    return builder.as_markup()
