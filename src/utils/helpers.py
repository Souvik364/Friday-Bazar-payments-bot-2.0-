"""
Friday Bazar Payments - Utility Functions
==========================================
Helper functions for QR generation, formatting, etc.
Optimized with async operations and caching
"""

import qrcode
from io import BytesIO
from aiogram.types import BufferedInputFile
import asyncio
from datetime import datetime, timedelta
from typing import Dict

# QR code cache to avoid regenerating identical QR codes
_qr_cache: Dict[str, bytes] = {}


def _generate_qr_sync(upi_id: str, name: str, amount: float, order_id: str) -> bytes:
    """
    Synchronous QR generation (called in thread pool)
    
    Args:
        upi_id: UPI ID for payment
        name: Merchant name
        amount: Payment amount
        order_id: Unique order ID
        
    Returns:
        PNG image bytes
    """
    upi_string = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&tn={order_id}&cu=INR"
    
    # Generate QR code with optimized settings
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,  # Reduced from 10 for faster generation
        border=3,    # Reduced from 4
    )
    qr.add_data(upi_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    bio = BytesIO()
    img.save(bio, 'PNG', optimize=True)
    bio.seek(0)
    
    return bio.read()


async def generate_upi_qr_async(upi_id: str, name: str, amount: float, order_id: str) -> BufferedInputFile:
    """
    Generate UPI payment QR code asynchronously with caching
    
    This function runs the QR generation in a thread pool to avoid blocking
    the event loop. QR codes are cached based on UPI ID and amount.
    
    Args:
        upi_id: UPI ID for payment
        name: Merchant name
        amount: Payment amount
        order_id: Unique order ID
        
    Returns:
        BufferedInputFile ready for Telegram upload
    """
    # Create cache key (same QR for same UPI + amount)
    cache_key = f"{upi_id}_{amount}"
    
    # Check cache first
    if cache_key in _qr_cache:
        image_bytes = _qr_cache[cache_key]
    else:
        # Generate QR in thread pool (non-blocking)
        loop = asyncio.get_event_loop()
        image_bytes = await loop.run_in_executor(
            None,
            _generate_qr_sync,
            upi_id, name, amount, order_id
        )
        
        # Cache for future use (limit cache size to 100 entries)
        if len(_qr_cache) > 100:
            # Remove oldest entry
            _qr_cache.pop(next(iter(_qr_cache)))
        _qr_cache[cache_key] = image_bytes
    
    return BufferedInputFile(image_bytes, filename=f"payment_qr_{order_id}.png")


def generate_upi_qr(upi_id: str, name: str, amount: float, order_id: str) -> BufferedInputFile:
    """
    Legacy synchronous QR generation (deprecated)
    
    Use generate_upi_qr_async() instead for better performance.
    Keeping this for backward compatibility.
    """
    image_bytes = _generate_qr_sync(upi_id, name, amount, order_id)
    return BufferedInputFile(image_bytes, filename=f"payment_qr_{order_id}.png")


def format_currency(amount: float) -> str:
    """Format amount as Indian Rupees"""
    return f"₹{amount:,.2f}"


def calculate_commission(amount: float, percent: float) -> float:
    """Calculate commission amount"""
    return round((amount * percent) / 100, 2)


async def payment_timer(seconds: int, callback):
    """
    Async timer for payment expiration
    Calls callback function after specified seconds
    """
    await asyncio.sleep(seconds)
    await callback()


def format_user_mention(user_id: int, username: str = None, first_name: str = None) -> str:
    """Format user mention for messages"""
    if username:
        return f"@{username}"
    elif first_name:
        return f"[{first_name}](tg://user?id={user_id})"
    else:
        return f"User {user_id}"


def get_expiry_time(minutes: int) -> str:
    """Get formatted expiry time"""
    expiry = datetime.now() + timedelta(minutes=minutes)
    return expiry.strftime("%I:%M %p")

