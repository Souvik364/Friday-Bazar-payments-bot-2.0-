"""
Friday Bazar Payments - Dynamic Button Handler
===============================================
Handles custom button clicks added by admin
"""

from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text)
async def handle_custom_buttons(message: Message):
    """
    Handle clicks on custom buttons added via /menu_add
    This catches any unhandled button text
    """
    import json
    from pathlib import Path
    
    button_text = message.text
    
    # Load custom buttons from JSON
    try:
        menus_file = Path("data/menus.json")
        if menus_file.exists():
            with open(menus_file, 'r', encoding='utf-8') as f:
                menus_data = json.load(f)
                custom_buttons = menus_data.get("custom_buttons", [])
                
                # Check if clicked button is a custom button
                for button in custom_buttons:
                    if button["text"] == button_text:
                        # Custom button clicked!
                        action_id = button["action"]
                        
                        # Send response about the custom button
                        response_text = (
                            f"🎯 **{button['text']}**\n\n"
                            f"This is a custom button added by admin!\n\n"
                            f"📋 Action ID: `{action_id}`\n\n"
                            "💡 **For Admins:**\n"
                            "To customize this button's action:\n"
                            "1. Edit handlers to respond to '{action_id}'\n"
                            "2. Or link to existing service\n\n"
                            "Example:\n"
                            "```python\n"
                            "@router.message(F.text == '{button_text}')\n"
                            "async def handle_{action_id}(message):\n"
                            "    # Your custom logic here\n"
                            "    await message.answer('Response')\n"
                            "```"
                        )
                        
                        await message.answer(
                            response_text.format(
                                button_text=button['text'],
                                action_id=action_id
                            ),
                            parse_mode="Markdown"
                        )
                        return  # Button handled
    except Exception as e:
        pass  # Not a custom button, let other handlers process it
