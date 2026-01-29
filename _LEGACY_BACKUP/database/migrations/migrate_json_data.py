"""
Migrate existing JSON data to database
======================================
Imports users.json and orders.json into SQLite database
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db_manager import db
from database.models import User, Payment, PaymentStatus


async def migrate_users():
    """Migrate users from users.json to database"""
    users_file = Path("data/users.json")
    
    if not users_file.exists():
        print("[INFO] users.json not found, skipping user migration")
        return 0
    
    with open(users_file, 'r', encoding='utf-8') as f:
        users_data = json.load(f)
    
    migrated = 0
    for user_id_str, user_data in users_data.items():
        try:
            user_id = int(user_id_str)
            
            # Check if user already exists
            existing_user = await db.get_user(user_id)
            if existing_user:
                print(f"[SKIP] User {user_id} already exists")
                continue
            
            # Create user model
            user = User(
                user_id=user_id,
                username=user_data.get('username'),
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                coins=float(user_data.get('coins', 0)),
                referrer_id=user_data.get('referred_by'),
                total_referrals=user_data.get('total_referrals', 0),
                total_earnings=float(user_data.get('total_earnings', 0)),
                is_banned=user_data.get('is_banned', False),
                has_premium=user_data.get('has_premium', False),
                premium_expires_at=datetime.fromisoformat(user_data['premium_expires_at']) 
                                    if user_data.get('premium_expires_at') else None,
                created_at=datetime.fromisoformat(user_data['joined_at']) 
                           if user_data.get('joined_at') else datetime.now()
            )
            
            await db.create_user(user)
            migrated += 1
            print(f"[OK] Migrated user {user_id} - {user.first_name}")
            
        except Exception as e:
            print(f"[ERROR] Failed to migrate user {user_id_str}: {e}")
    
    return migrated


async def migrate_orders():
    """Migrate orders from orders.json to payments table"""
    orders_file = Path("data/orders.json")
    
    if not orders_file.exists():
        print("[INFO] orders.json not found, skipping orders migration")
        return 0
    
    with open(orders_file, 'r', encoding='utf-8') as f:
        orders_data = json.load(f)
    
    migrated = 0
    for order_id, order_data in orders_data.items():
        try:
            # Check if payment already exists
            existing_payment = await db.get_payment(order_id)
            if existing_payment:
                print(f"[SKIP] Payment {order_id} already exists")
                continue
            
            # Map status
            status_map = {
                'pending': PaymentStatus.PENDING,
                'approved': PaymentStatus.APPROVED,
                'rejected': PaymentStatus.REJECTED
            }
            status = status_map.get(order_data.get('status', 'pending'), PaymentStatus.PENDING)
            
            # Create payment model
            payment = Payment(
                payment_id=order_id,
                user_id=order_data.get('user_id'),
                plan_id=order_data.get('service_id', 'legacy_plan'),  # Will need to map services to plans
                amount=float(order_data.get('amount', 0)),
                screenshot_file_id=order_data.get('screenshot_file_id'),
                status=status,
                admin_id=order_data.get('approved_by'),
                user_details=order_data.get('user_email'),
                created_at=datetime.fromisoformat(order_data['created_at']) 
                           if order_data.get('created_at') else datetime.now(),
                processed_at=datetime.fromisoformat(order_data['approved_at']) 
                            if order_data.get('approved_at') else None
            )
            
            await db.create_payment(payment)
            migrated += 1
            print(f"[OK] Migrated order {order_id}")
            
        except Exception as e:
            print(f"[ERROR] Failed to migrate order {order_id}: {e}")
    
    return migrated


async def main():
    """Run migration"""
    print("=" * 50)
    print("DATABASE MIGRATION: JSON to SQLite")
    print("=" * 50)
    
    # Initialize database
    await db.initialize()
    
    # Migrate users
    print("\n[1/2] Migrating users...")
    users_count = await migrate_users()
    print(f"✓ Migrated {users_count} users")
    
    # Migrate orders
    print("\n[2/2] Migrating orders...")
    orders_count = await migrate_orders()
    print(f"✓ Migrated {orders_count} orders")
    
    print("\n" + "=" * 50)
    print(f"MIGRATION COMPLETE")
    print(f"Users: {users_count} | Orders: {orders_count}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
