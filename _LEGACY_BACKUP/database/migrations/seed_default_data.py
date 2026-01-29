"""
Seed Default Menu Data
======================
Creates initial menu structure for Friday Bazar bot
"""

import asyncio
import uuid
from datetime import datetime
import sys
from pathlib import Path
import os

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')  # Set console to UTF-8
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db_manager import db
from database.models import Menu, Button, MenuContentType, ButtonType, PaymentPlan, AdminUser, AdminRole
from src.config import ADMIN_IDS


def generate_id(prefix: str = "") -> str:
    """Generate unique ID"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


async def seed_admins():
    """Create admin users from config"""
    print("\n[ADMINS] Creating admin users...")
    
    for admin_id in ADMIN_IDS:
        existing = await db.get_admin(admin_id)
        if existing:
            print(f"  [SKIP] Admin {admin_id} already exists")
            continue
        
        admin = AdminUser(
            admin_id=admin_id,
            role=AdminRole.SUPER_ADMIN,
            permissions={}
        )
        await db.create_admin(admin)
        print(f"  [OK] Created super admin: {admin_id}")


async def seed_main_menu():
    """Create main menu"""
    print("\n[MENU] Creating Main Menu...")
    
    # Check if already exists
    existing = await db.get_menu_by_name("Main Menu")
    if existing:
        print("  [SKIP] Main Menu already exists")
        return existing.menu_id
    
    # Create main menu
    main_menu = Menu(
        menu_id=generate_id("menu"),
        name="Main Menu",
        description="Welcome to Friday Bazar! 🛍️\n\nYour one-stop shop for premium subscriptions at unbeatable prices.\n\n💎 Premium Services\n🎁 Referral Rewards\n📞 24/7 Support",
        content_type=MenuContentType.TEXT,
        content_data="Welcome to Friday Bazar! 🛍️\n\nYour one-stop shop for premium subscriptions at unbeatable prices.\n\n💎 Premium Services\n🎁 Referral Rewards\n📞 24/7 Support",
        is_active=True,
        position=0
    )
    await db.create_menu(main_menu)
    print(f"  [OK] Created Main Menu (ID: {main_menu.menu_id})")
    
    # Create buttons for main menu
    buttons = [
        Button(
            button_id=generate_id("btn"),
            menu_id=main_menu.menu_id,
            text="🛒 Start Payment",
            type=ButtonType.SUBMENU,
            action_data="services_menu",  # Will create this next
            row=0,
            column=0
        ),
        Button(
            button_id=generate_id("btn"),
            menu_id=main_menu.menu_id,
            text="💰 My Friday Coins",
            type=ButtonType.ACTION,
            action_data="show_coins",
            row=1,
            column=0
        ),
        Button(
            button_id=generate_id("btn"),
            menu_id=main_menu.menu_id,
            text="🔗 Referral Link",
            type=ButtonType.ACTION,
            action_data="show_referral",
            row=1,
            column=1
        ),
        Button(
            button_id=generate_id("btn"),
            menu_id=main_menu.menu_id,
            text="🆘 Help",
            type=ButtonType.ACTION,
            action_data="show_help",
            row=2,
            column=0
        ),
        Button(
            button_id=generate_id("btn"),
            menu_id=main_menu.menu_id,
            text="📞 Contact Support",
            type=ButtonType.ACTION,
            action_data="show_contact",
            row=2,
            column=1
        ),
    ]
    
    for btn in buttons:
        await db.create_button(btn)
        print(f"  [OK] Added button: {btn.text}")
    
    return main_menu.menu_id


async def seed_services_menu():
    """Create services/plans menu"""
    print("\n[MENU] Creating Services Menu...")
    
    existing = await db.get_menu_by_name("Premium Services")
    if existing:
        print("  [SKIP] Premium Services menu already exists")
        return existing.menu_id
    
    services_menu = Menu(
        menu_id="services_menu",
        name="Premium Services",
        description="🎬 Choose your premium service:\n\nAll plans come with instant delivery and 24/7 support!",
        content_type=MenuContentType.TEXT,
        content_data="🎬 Choose your premium service:\n\nAll plans come with instant delivery and 24/7 support!",
        is_active=True,
        position=1
    )
    await db.create_menu(services_menu)
    print(f"  [OK] Created Services Menu (ID: {services_menu.menu_id})")
    
    # Create sample payment plans
    plans = [
        {
            "name": "YouTube Premium",
            "duration_days": 365,
            "price": 25.0,
            "original_price": 129.0,
            "features": [
                "Ad-free videos",
                "Background playback",
                "YouTube Music Premium",
                "Offline downloads"
            ],
            "button_text": "Buy YouTube - ₹25"
        },
        {
            "name": "Zee5 Premium",
            "duration_days": 365,
            "price": 180.0,
            "original_price": 299.0,
            "features": [
                "Full HD streaming",
                "5 screens",
                "Exclusive content",
                "No ads"
            ],
            "button_text": "Buy Zee5 - ₹180"
        },
        {
            "name": "Spotify Premium",
            "duration_days": 365,
            "price": 149.0,
            "original_price": 1189.0,
            "features": [
                "Ad-free music",
                "Unlimited skips",
                "Offline mode",
                "High quality audio"
            ],
            "button_text": "Buy Spotify - ₹149"
        },
    ]
    
    row = 0
    for plan_data in plans:
        plan_id = generate_id("plan")
        
        plan = PaymentPlan(
            plan_id=plan_id,
            name=plan_data["name"],
            duration_days=plan_data["duration_days"],
            price=plan_data["price"],
            original_price=plan_data["original_price"],
            features=plan_data["features"],
            button_text=plan_data["button_text"],
            is_active=True
        )
        await db.create_plan(plan)
        print(f"  [OK] Created plan: {plan.name}")
        
        # Create button for this plan in services menu
        btn = Button(
            button_id=generate_id("btn"),
            menu_id=services_menu.menu_id,
            text=f"🎬 {plan_data['name']}",
            type=ButtonType.PAYMENT,
            action_data=plan_id,
            row=row,
            column=0
        )
        await db.create_button(btn)
        print(f"  [OK] Added button: {btn.text}")
        row += 1
    
    # Add back button
    back_btn = Button(
        button_id=generate_id("btn"),
        menu_id=services_menu.menu_id,
        text="◀️ Back to Main Menu",
        type=ButtonType.SUBMENU,
        action_data="main_menu_back",  # Special action to go back
        row=row,
        column=0
    )
    await db.create_button(back_btn)
    print(f"  [OK] Added back button")
    
    return services_menu.menu_id


async def main():
    """Run seeding"""
    print("=" * 50)
    print("SEEDING DEFAULT DATA")
    print("=" * 50)
    
    # Initialize database
    await db.initialize()
    
    # Seed data
    await seed_admins()
    await seed_main_menu()
    await seed_services_menu()
    
    print("\n" + "=" * 50)
    print("SEEDING COMPLETE ✓")
    print("=" * 50)
    print("\n[NEXT STEPS]")
    print("1. Run the bot: python main.py")
    print("2. Type /start to see the new dynamic menu")
    print("3. Type /admin to access admin panel")


if __name__ == "__main__":
    asyncio.run(main())
