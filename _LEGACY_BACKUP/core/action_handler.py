"""
Action Handler
==============
Routes button clicks to appropriate handlers
"""

from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from typing import Optional

from database.db_manager import db
from database.models import ButtonType
from core.menu_renderer import render_menu
from core.payment_integration import handle_payment_confirmation, start_payment_timer


async def handle_callback(callback: CallbackQuery, bot: Bot) -> bool:
    """
    Main callback handler routing
    
    Callback data format: "type:action_data"
    Examples:
        - "submenu:menu_abc123"
        - "payment:plan_xyz789"
        - "action:show_coins"
    
    Returns:
        bool: Whether callback was handled
    """
    try:
        # Parse callback data
        if ":" not in callback.data:
            await callback.answer("Invalid action")
            return False
        
        action_type, action_data = callback.data.split(":", 1)
        
        # Special handling for confirm_payment (integrates with existing payment flow)
        if action_type == "confirm_payment":
            return await handle_payment_confirmation(callback, action_data, bot)
        
        # Route to appropriate handler
        if action_type == ButtonType.SUBMENU.value:
            return await handle_submenu(callback, action_data, bot)
        
        elif action_type == ButtonType.MESSAGE.value:
            return await handle_message(callback, action_data, bot)
        
        elif action_type == ButtonType.PAYMENT.value:
            return await handle_payment(callback, action_data, bot)
        
        elif action_type == ButtonType.ACTION.value:
            return await handle_custom_action(callback, action_data, bot)
        
        else:
            await callback.answer("Unknown action type")
            return False
        
    except Exception as e:
        print(f"[ERROR] Callback handling failed: {e}")
        await callback.answer("An error occurred. Please try again.")
        return False


async def handle_submenu(callback: CallbackQuery, menu_id: str, bot: Bot) -> bool:
    """Handle submenu navigation"""
    
    # Special handling for "back to main menu"
    if menu_id == "main_menu_back":
        # Get the actual main menu
        main_menu = await db.get_menu_by_name("Main Menu")
        if main_menu:
            menu_id = main_menu.menu_id
        else:
            await callback.answer("Main menu not found!")
            return False
    
    # Render the submenu
    success = await render_menu(
        user_id=callback.from_user.id,
        menu_id=menu_id,
        bot=bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        edit=True
    )
    
    if success:
        await callback.answer()
    else:
        await callback.answer("Failed to load menu")
    
    return success


async def handle_message(callback: CallbackQuery, message_text: str, bot: Bot) -> bool:
    """Handle send message action"""
    await bot.send_message(
        callback.message.chat.id,
        message_text,
        parse_mode="HTML"
    )
    await callback.answer("Message sent!")
    return True


async def handle_payment(callback: CallbackQuery, plan_id: str, bot: Bot) -> bool:
    """Handle payment flow trigger"""
    # Get payment plan
    plan = await db.get_plan(plan_id)
    if not plan:
        await callback.answer("Payment plan not found!")
        return False
    
    # Display plan details
    plan_text = f"""
💎 <b>{plan.name}</b>

<b>Price:</b> ₹{plan.price}
{f'<s>₹{plan.original_price}</s>' if plan.original_price else ''}

<b>Duration:</b> {plan.duration_days} days

<b>Features:</b>
"""
    
    for feature in plan.features:
        plan_text += f"✅ {feature}\n"
    
    plan_text += f"\n💳 <b>Total Amount: ₹{plan.price}</b>"
    
    # Import here to avoid circular dependency
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Pay ₹{plan.price} Now", callback_data=f"confirm_payment:{plan_id}")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="submenu:services_menu")]
    ])
    
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=plan_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await callback.answer()
    return True


async def handle_custom_action(callback: CallbackQuery, action_name: str, bot: Bot) -> bool:
    """
    Handle custom actions (referrals, help, contact, etc.)
    
    Actions:
        - show_coins: Display coin balance
        - show_referral: Show referral link
        - show_help: Help menu
        - show_contact: Contact info
    """
    user_id = callback.from_user.id
    
    if action_name == "show_coins":
        return await show_coins(callback, bot)
    
    elif action_name == "show_referral":
        return await show_referral(callback, bot)
    
    elif action_name == "show_help":
        return await show_help(callback, bot)
    
    elif action_name == "show_contact":
        return await show_contact(callback, bot)
    
    else:
        await callback.answer(f"Action '{action_name}' not implemented yet")
        return False


async def show_coins(callback: CallbackQuery, bot: Bot) -> bool:
    """Show user's coin balance"""
    user = await db.get_user(callback.from_user.id)
    
    if not user:
        await callback.answer("User not found!")
        return False
    
    message = f"""
💰 <b>Your Friday Coins</b>

<b>Balance:</b> ₹{user.coins:.2f}
<b>Total Earnings:</b> ₹{user.total_earnings:.2f}
<b>Total Referrals:</b> {user.total_referrals}

💡 <i>1 Coin = ₹1</i>

Earn more by referring friends! You get 10% of their purchase amount.
"""
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    
    await callback.message.edit_text(message, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
    return True


async def show_referral(callback: CallbackQuery, bot: Bot) -> bool:
    """Show user's referral link"""
    user_id = callback.from_user.id
    
    # Import config for bot username
    from src.config import BOT_USERNAME
    
    referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    
    message = f"""
🔗 <b>Your Referral Link</b>

Share this link with friends:
<code>{referral_link}</code>

<b>How it works:</b>
✅ Friend clicks your link
✅ Friend makes a purchase
✅ You earn 10% coins instantly!

💰 <b>Example:</b> Friend buys ₹100 plan → You get ₹10
"""
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    
    await callback.message.edit_text(message, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
    return True


async def show_help(callback: CallbackQuery, bot: Bot) -> bool:
    """Show help information"""
    message = """
🆘 <b>Help & Support</b>

<b>How to Buy:</b>
1️⃣ Click "🛒 Start Payment"
2️⃣ Choose your service
3️⃣ Pay via UPI and upload screenshot
4️⃣ Get instant access!

<b>Payment Methods:</b>
💳 UPI (PhonePe, GPay, Paytm)

<b>Delivery Time:</b>
⚡ Within 5-30 minutes after verification

<b>Need Help?</b>
📞 Click "Contact Support" for assistance
"""
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    
    await callback.message.edit_text(message, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
    return True


async def show_contact(callback: CallbackQuery, bot: Bot) -> bool:
    """Show contact information"""
    from src.config import SUPPORT_USERNAME
    
    message = f"""
📞 <b>Contact Support</b>

For any queries, issues, or support:

👤 @{SUPPORT_USERNAME}

<b>Support Hours:</b>
🕐 24/7 Available

<b>Response Time:</b>
⚡ Usually within 1 hour

We're here to help! 😊
"""
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    
    await callback.message.edit_text(message, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
    return True
