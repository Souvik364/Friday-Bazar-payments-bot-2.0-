"""
Clean Main Menu Buttons
========================
Remove all buttons except "Start Payment" from Main Menu
"""

import asyncio
import sys
import os

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from database.db_manager import db


async def clean_main_menu():
    """Remove unwanted buttons from main menu"""
    await db.initialize()
    
    # Get Main Menu
    main_menu = await db.get_menu_by_name("Main Menu")
    if not main_menu:
        print("[ERROR] Main Menu not found!")
        return
    
    print(f"[INFO] Found Main Menu: {main_menu.menu_id}")
    
    # Get all buttons
    buttons = await db.get_menu_buttons(main_menu.menu_id, active_only=False)
    print(f"[INFO] Found {len(buttons)} buttons")
    
    # Delete all buttons except "Start Payment"
    deleted = 0
    kept = 0
    
    for button in buttons:
        if "Start Payment" in button.text or "🛒" in button.text:
            print(f"[KEEP] {button.text}")
            kept += 1
        else:
            await db.delete_button(button.button_id)
            print(f"[DELETE] {button.text}")
            deleted += 1
    
    print(f"\n[DONE] Kept {kept} button(s), Deleted {deleted} button(s)")
    print("\nRestart your bot to see the changes!")


if __name__ == "__main__":
    asyncio.run(clean_main_menu())
