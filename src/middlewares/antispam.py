"""
Friday Bazar Payments - Anti-Spam Middleware
=============================================
Rate limiting to prevent spam and abuse
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from datetime import datetime, timedelta
from collections import defaultdict

from src.config import ADMIN_IDS


class AntiSpamMiddleware(BaseMiddleware):
    """
    Rate limiting middleware
    Tracks message count per user and blocks if threshold exceeded
    """
    
    def __init__(self, rate_limit: int = 10, time_window: int = 60):
        """
        Args:
            rate_limit: Maximum messages allowed in time window
            time_window: Time window in seconds
        """
        super().__init__()
        self.rate_limit = rate_limit
        self.time_window = time_window
        
        # Store: user_id -> list of message timestamps
        self.message_history: Dict[int, list[datetime]] = defaultdict(list)
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        # Skip rate limiting for admins
        if user_id in ADMIN_IDS:
            return await handler(event, data)
        
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=self.time_window)
        
        # Clean old messages outside time window
        self.message_history[user_id] = [
            ts for ts in self.message_history[user_id]
            if ts > cutoff_time
        ]
        
        # Check if user exceeded rate limit
        if len(self.message_history[user_id]) >= self.rate_limit:
            await event.answer(
                "⚠️ **Slow down!**\n\n"
                f"You're sending messages too quickly. Please wait a moment.\n"
                f"Limit: {self.rate_limit} messages per {self.time_window} seconds.",
                parse_mode="Markdown"
            )
            return  # Block the message
        
        # Add current message timestamp
        self.message_history[user_id].append(now)
        
        # Process the message
        return await handler(event, data)
