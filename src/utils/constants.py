"""
Friday Bazar Payments - Constants and Text Templates
====================================================
Centralized emojis, messages, and UI text for consistency
"""

# ==================== EMOJIS ====================

# Status & Feedback
EMOJI_SUCCESS = "✅"
EMOJI_ERROR = "❌"
EMOJI_WARNING = "⚠️"
EMOJI_INFO = "ℹ️"
EMOJI_LOADING = "⏳"

# Actions & Navigation
EMOJI_PAYMENT = "💸"
EMOJI_BACK = "🔙"
EMOJI_CLOSE = "❌"
EMOJI_CART = "🛒"
EMOJI_HELP = "🆘"

# Features
EMOJI_COINS = "💰"
EMOJI_REFERRAL = "🔗"
EMOJI_GIFT = "🎁"
EMOJI_CONTACT = "📞"
EMOJI_TERMS = "📜"
EMOJI_TELEGRAM = "📱"

# Payment & Orders
EMOJI_QR = "📲"
EMOJI_SCREENSHOT = "📸"
EMOJI_ORDER = "🆔"
EMOJI_PRICE = "💵"
EMOJI_TIMER = "⏰"

# Services
EMOJI_YOUTUBE = "▶️"
EMOJI_NETFLIX = "🎬"
EMOJI_SPOTIFY = "🎵"
EMOJI_CANVA = "🎨"
EMOJI_TV = "📺"

# Admin
EMOJI_ADMIN = "👨‍💼"
EMOJI_APPROVE = "✅"
EMOJI_REJECT = "❌"
EMOJI_PENDING = "🔔"


# ==================== BUTTON LABELS ====================

# Main Menu
BTN_START_PAYMENT = f"{EMOJI_CART} Start Payment"
BTN_TELEGRAM_ACCOUNTS = f"{EMOJI_TELEGRAM} Telegram Accounts"
BTN_MY_COINS = f"{EMOJI_COINS} My Friday Coins"
BTN_REFERRAL_LINK = f"{EMOJI_REFERRAL} Referral Link"
BTN_TERMS = f"{EMOJI_TERMS} Terms of Service"
BTN_CONTACT = f"{EMOJI_CONTACT} Contact"
BTN_HELP = f"{EMOJI_HELP} Help"

# Navigation
BTN_BACK_TO_MENU = f"{EMOJI_BACK} Back to Main Menu"
BTN_BACK_TO_SERVICES = f"{EMOJI_BACK} Back to Services"
BTN_CLOSE = f"{EMOJI_CLOSE} Close"

# Payment Flow
BTN_UPLOAD_SCREENSHOT = f"{EMOJI_SUCCESS} I've Paid - Upload Screenshot"
BTN_CANCEL_ORDER = f"{EMOJI_ERROR} Cancel Order"

# Admin
BTN_APPROVE = f"{EMOJI_APPROVE} Approve"
BTN_REJECT = f"{EMOJI_REJECT} Reject"


# ==================== MESSAGE TEMPLATES ====================

# Loading Messages
MSG_PROCESSING = f"{EMOJI_LOADING} Processing..."
MSG_LOADING_QR = f"{EMOJI_LOADING} Generating payment QR code..."
MSG_LOADING_SERVICE = f"{EMOJI_LOADING} Loading service details..."
MSG_PLEASE_WAIT = f"{EMOJI_LOADING} Please wait..."

# Success Messages
MSG_PAYMENT_SUCCESS = f"{EMOJI_SUCCESS} Payment approved! Your subscription is now active."
MSG_SCREENSHOT_RECEIVED = f"{EMOJI_SUCCESS} Screenshot received! We're verifying your payment."
MSG_ORDER_CREATED = f"{EMOJI_SUCCESS} Order created successfully!"
MSG_OPERATION_CANCELLED = f"{EMOJI_SUCCESS} Operation cancelled."

# Error Messages
MSG_ERROR_GENERIC = f"{EMOJI_ERROR} Oops! Something went wrong. Please try again or contact support."
MSG_ERROR_UNAUTHORIZED = f"{EMOJI_ERROR} You are not authorized for this action."
MSG_ERROR_SERVICE_NOT_FOUND = f"{EMOJI_ERROR} Service not found."
MSG_ERROR_ORDER_NOT_FOUND = f"{EMOJI_ERROR} Order not found."
MSG_ERROR_ORDER_EXPIRED = f"{EMOJI_ERROR} This order has expired."
MSG_ERROR_ALREADY_PROCESSED = f"{EMOJI_INFO} This order is already being processed."

# Info Messages
MSG_NO_ACTIVE_OPERATION = f"{EMOJI_INFO} No active operation to cancel."
MSG_COMING_SOON = f"{EMOJI_INFO} Coming Soon! We're working on bringing you this feature."

# Payment Instructions
MSG_PAYMENT_IMPORTANT = f"{EMOJI_WARNING} **Important:**"
MSG_PAYMENT_INSTRUCTIONS = (
    "• Use the exact amount shown\n"
    "• Keep your payment screenshot ready\n"
    "• Click 'I've Paid' after completing payment"
)


# ==================== TEXT TEMPLATES ====================

def get_welcome_text(first_name: str) -> str:
    """Get personalized welcome message"""
    return (
        f"Hey, {first_name}!\n\n"
        "🌟 Welcome to Friday Bazar Payment Bot!\n"
        "🌟\n"
        "📜 Securely make payments using UPI!\n\n"
        "👇 Choose an option below:"
    )


def get_payment_details_text(service_name: str, plan_duration: str, amount: float, 
                             order_id: str, upi_id: str, expiry_time: str, 
                             timeout_minutes: int) -> str:
    """Get payment details message"""
    return (
        f"💳 **Payment Details**\n\n"
        f"🛍️ Service: **{service_name}**\n"
        f"⏱️ Plan: **{plan_duration}**\n"
        f"💰 Amount: **₹{amount:.2f}**\n"
        f"🆔 Order ID: `{order_id}`\n\n"
        f"⏰ Complete payment before **{expiry_time}**\n"
        f"({timeout_minutes} minutes)\n\n"
        f"📲 **Scan the QR code** or pay to:\n"
        f"UPI ID: `{upi_id}`\n\n"
        f"{MSG_PAYMENT_IMPORTANT}\n"
        f"{MSG_PAYMENT_INSTRUCTIONS}"
    )


def get_screenshot_prompt_text() -> str:
    """Get screenshot upload prompt"""
    return (
        f"{EMOJI_SCREENSHOT} **Upload Payment Screenshot**\n\n"
        "Please send a clear screenshot of your payment confirmation.\n\n"
        f"{EMOJI_WARNING} Make sure the screenshot shows:\n"
        "• Transaction amount\n"
        "• UPI transaction ID\n"
        "• Date and time"
    )


def get_verification_message_text() -> str:
    """Get payment verification message"""
    return (
        f"{EMOJI_SUCCESS} **Screenshot Received!**\n\n"
        "Your payment is being verified by our team.\n"
        "You'll be notified once approved (usually within 5-10 minutes)."
    )


def get_payment_expired_text(order_id: str) -> str:
    """Get payment expiry message"""
    return (
        f"{EMOJI_TIMER} **Payment Expired**\n\n"
        f"Order `{order_id}` has expired.\n"
        "Please create a new order if you still want to purchase."
    )


def get_payment_rejected_text(order_id: str) -> str:
    """Get payment rejection message"""
    return (
        f"{EMOJI_ERROR} **Payment Verification Failed**\n\n"
        f"Unfortunately, we couldn't verify your payment for order `{order_id}`.\n\n"
        "Possible reasons:\n"
        "• Incorrect amount paid\n"
        "• Screenshot unclear\n"
        "• Payment not received\n\n"
        "Please contact support if you believe this is an error."
    )


def get_admin_approval_text(order_id: str, service_name: str, plan_duration: str, 
                            amount: float, support_username: str) -> str:
    """Get admin approval notification for user"""
    return (
        f"{EMOJI_SUCCESS} **Payment Approved!**\n\n"
        f"🎉 Your payment has been verified.\n\n"
        "**Order Details:**\n"
        f"🆔 Order ID: `{order_id}`\n"
        f"🛍️ Service: {service_name}\n"
        f"⏱️ Plan: {plan_duration}\n"
        f"💰 Amount Paid: ₹{amount:.2f}\n\n"
        f"📢 **Next Step - Activation:**\n"
        f"👉 Contact: @{support_username}\n\n"
        "**Please mention:**\n"
        f"• Your Order ID: `{order_id}`\n"
        f"• Service: {service_name}\n"
        "• Your Gmail (for YouTube Premium)\n\n"
        "Our team will activate your subscription within 24 hours!"
    )
