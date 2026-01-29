"""
Friday Bazar Payments - Language Middleware
===========================================
Injects user's language preference into handler context
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from src.services.db import db
from src.data.translations import get_text


class LanguageMiddleware(BaseMiddleware):
    """
    Middleware to inject user's language preference into handler data
    Provides translation helper function to all handlers
    """
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Get user ID
        user_id = event.from_user.id
        
        # Get user language from database (default to English)
        try:
            user = await db.get_user(user_id)
            lang = user.get('language', 'en')
        except:
            lang = 'en'
        
        # Inject language and translation helper into handler data
        data['lang'] = lang
        data['t'] = lambda key, **kwargs: get_text(key, lang, **kwargs)
        
        # Call the handler
        return await handler(event, data)
