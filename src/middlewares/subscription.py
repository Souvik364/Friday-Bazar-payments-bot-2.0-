"""
Friday Bazar Payments - Subscription Middleware
================================================
Protects premium features by checking subscription status
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from src.services.subscription import subscription_service


class SubscriptionMiddleware(BaseMiddleware):
    """
    Middleware to protect premium-only handlers
    Add this middleware only to specific routers that need protection
    """
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        # Check if user has active subscription
        is_active = await subscription_service.is_subscription_active(user_id)
        
        if not is_active:
            # Block access - subscription required
            error_msg = (
                "🔒 **Subscription Required**\n\n"
                "This feature requires an active subscription.\n\n"
                "Get started: Tap 🛒 **Start Payment** to subscribe!"
            )
            
            if isinstance(event, Message):
                await event.answer(error_msg, parse_mode="Markdown")
            else:  # CallbackQuery
                await event.answer(error_msg, show_alert=True)
            
            return  # Block the action
        
        # User has active subscription, proceed
        return await handler(event, data)
