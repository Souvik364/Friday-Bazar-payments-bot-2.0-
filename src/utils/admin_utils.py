"""
Friday Bazar Payments - Admin Helpers
======================================
Decorators and utilities for admin features
"""

import functools
import json
import uuid
import aiofiles
from datetime import datetime
from pathlib import Path
from aiogram.types import Message, CallbackQuery

from src.config import ADMIN_IDS

async def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

def admin_only(func):
    """Decorator for admin-only handlers"""
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        # Determine user_id based on event type
        if isinstance(event, Message):
            user_id = event.from_user.id
            is_valid = await is_admin(user_id)
            if not is_valid:
                # Silent ignore or safe reply
                return
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            is_valid = await is_admin(user_id)
            if not is_valid:
                await event.answer("❌ Access Denied", show_alert=True)
                return
        else:
            # Fallback for other event types if any
            return 
            
        return await func(event, *args, **kwargs)
    return wrapper

async def log_admin_action(admin_id: int, admin_name: str, action_type: str, details: dict):
    """Log admin actions to file"""
    log_file = Path("logs/admin_actions.json")
    
    # Ensure directory exists
    log_file.parent.mkdir(exist_ok=True, parents=True)
    
    action_entry = {
        "action_id": str(uuid.uuid4()),
        "admin_id": admin_id,
        "admin_username": admin_name,
        "action_type": action_type,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    
    # Append to log file (loading entire file first - simple approach for now)
    try:
        if not log_file.exists():
            current_logs = {"actions": []}
        else:
            async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                current_logs = json.loads(content) if content else {"actions": []}
        
        current_logs["actions"].append(action_entry)
        
        async with aiofiles.open(log_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(current_logs, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Failed to log admin action: {e}")
