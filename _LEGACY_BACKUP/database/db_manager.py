"""
Database Manager
================
Async SQLite database operations for Friday Bazar
"""

import aiosqlite
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from .models import (
    Menu, Button, PaymentPlan, UserSession, Payment, User, AdminUser,
    MenuContentType, ButtonType, PaymentStatus, AdminRole
)


class DatabaseManager:
    """Async database manager for all CRUD operations"""
    
    def __init__(self, db_path: str = "data/friday_bazar.db"):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(exist_ok=True)
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection context manager"""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        try:
            yield conn
        finally:
            await conn.close()
    
    async def initialize(self):
        """Initialize database with schema"""
        async with self.get_connection() as conn:
            # Create menus table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS menus (
                    menu_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    content_type TEXT NOT NULL DEFAULT 'text',
                    content_data TEXT NOT NULL,
                    parent_menu_id TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    position INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_menu_id) REFERENCES menus(menu_id)
                )
            """)
            
            # Create buttons table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS buttons (
                    button_id TEXT PRIMARY KEY,
                    menu_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    type TEXT NOT NULL,
                    action_data TEXT NOT NULL,
                    row INTEGER DEFAULT 0,
                    column INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (menu_id) REFERENCES menus(menu_id) ON DELETE CASCADE
                )
            """)
            
            # Create payment_plans table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS payment_plans (
                    plan_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    duration_days INTEGER NOT NULL,
                    price REAL NOT NULL,
                    original_price REAL,
                    features TEXT,
                    qr_code_file_id TEXT,
                    button_text TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create user_sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    user_id INTEGER PRIMARY KEY,
                    current_menu_id TEXT,
                    session_data TEXT,
                    state TEXT DEFAULT 'browsing',
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (current_menu_id) REFERENCES menus(menu_id)
                )
            """)
            
            # Create payments table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    plan_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    screenshot_file_id TEXT,
                    status TEXT DEFAULT 'pending',
                    admin_id INTEGER,
                    user_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES payment_plans(plan_id)
                )
            """)
            
            # Create users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    coins REAL DEFAULT 0.0,
                    referrer_id INTEGER,
                    total_referrals INTEGER DEFAULT 0,
                    total_earnings REAL DEFAULT 0.0,
                    is_banned BOOLEAN DEFAULT 0,
                    has_premium BOOLEAN DEFAULT 0,
                    premium_expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create admin_users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    admin_id INTEGER PRIMARY KEY,
                    role TEXT NOT NULL DEFAULT 'super_admin',
                    permissions TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_buttons_menu ON buttons(menu_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_referrer ON users(referrer_id)")
            
            await conn.commit()
            print("[OK] Database initialized successfully")
    
    # =================== MENU OPERATIONS ===================
    
    async def create_menu(self, menu: Menu) -> Menu:
        """Create a new menu"""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO menus (menu_id, name, description, content_type, content_data,
                                   parent_menu_id, is_active, position, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                menu.menu_id, menu.name, menu.description, menu.content_type.value,
                menu.content_data, menu.parent_menu_id, menu.is_active, menu.position,
                menu.created_at, menu.updated_at
            ))
            await conn.commit()
            return menu
    
    async def get_menu(self, menu_id: str) -> Optional[Menu]:
        """Get menu by ID"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM menus WHERE menu_id = ?", (menu_id,))
            row = await cursor.fetchone()
            if row:
                return Menu(**dict(row))
            return None
    
    async def get_menu_by_name(self, name: str) -> Optional[Menu]:
        """Get menu by name"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM menus WHERE name = ? AND is_active = 1", (name,))
            row = await cursor.fetchone()
            if row:
                return Menu(**dict(row))
            return None
    
    async def get_all_menus(self, active_only: bool = True) -> List[Menu]:
        """Get all menus"""
        async with self.get_connection() as conn:
            query = "SELECT * FROM menus"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY position, name"
            
            cursor = await conn.execute(query)
            rows = await cursor.fetchall()
            return [Menu(**dict(row)) for row in rows]
    
    async def update_menu(self, menu: Menu) -> Menu:
        """Update existing menu"""
        menu.updated_at = datetime.now()
        async with self.get_connection() as conn:
            await conn.execute("""
                UPDATE menus SET name = ?, description = ?, content_type = ?, content_data = ?,
                                  parent_menu_id = ?, is_active = ?, position = ?, updated_at = ?
                WHERE menu_id = ?
            """, (
                menu.name, menu.description, menu.content_type.value, menu.content_data,
                menu.parent_menu_id, menu.is_active, menu.position, menu.updated_at, menu.menu_id
            ))
            await conn.commit()
            return menu
    
    async def delete_menu(self, menu_id: str) -> bool:
        """Delete menu (soft delete - set inactive)"""
        async with self.get_connection() as conn:
            await conn.execute("UPDATE menus SET is_active = 0 WHERE menu_id = ?", (menu_id,))
            await conn.commit()
            return True
    
    # =================== BUTTON OPERATIONS ===================
    
    async def create_button(self, button: Button) -> Button:
        """Create a new button"""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO buttons (button_id, menu_id, text, type, action_data, row, column, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                button.button_id, button.menu_id, button.text, button.type.value,
                button.action_data, button.row, button.column, button.is_active, button.created_at
            ))
            await conn.commit()
            return button
    
    async def get_menu_buttons(self, menu_id: str, active_only: bool = True) -> List[Button]:
        """Get all buttons for a menu"""
        async with self.get_connection() as conn:
            query = "SELECT * FROM buttons WHERE menu_id = ?"
            params = [menu_id]
            
            if active_only:
                query += " AND is_active = 1"
            
            query += " ORDER BY row, column"
            
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            return [Button(**dict(row)) for row in rows]
    
    async def update_button(self, button: Button) -> Button:
        """Update existing button"""
        async with self.get_connection() as conn:
            await conn.execute("""
                UPDATE buttons SET text = ?, type = ?, action_data = ?, row = ?, column = ?, is_active = ?
                WHERE button_id = ?
            """, (
                button.text, button.type.value, button.action_data, button.row,
                button.column, button.is_active, button.button_id
            ))
            await conn.commit()
            return button
    
    async def delete_button(self, button_id: str) -> bool:
        """Delete button"""
        async with self.get_connection() as conn:
            await conn.execute("DELETE FROM buttons WHERE button_id = ?", (button_id,))
            await conn.commit()
            return True
    
    # =================== PAYMENT PLAN OPERATIONS ===================
    
    async def create_plan(self, plan: PaymentPlan) -> PaymentPlan:
        """Create a new payment plan"""
        async with self.get_connection() as conn:
            features_json = json.dumps(plan.features)
            await conn.execute("""
                INSERT INTO payment_plans (plan_id, name, duration_days, price, original_price,
                                           features, qr_code_file_id, button_text, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan.plan_id, plan.name, plan.duration_days, plan.price, plan.original_price,
                features_json, plan.qr_code_file_id, plan.button_text, plan.is_active,
                plan.created_at, plan.updated_at
            ))
            await conn.commit()
            return plan
    
    async def get_plan(self, plan_id: str) -> Optional[PaymentPlan]:
        """Get payment plan by ID"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM payment_plans WHERE plan_id = ?", (plan_id,))
            row = await cursor.fetchone()
            if row:
                data = dict(row)
                data['features'] = json.loads(data['features']) if data['features'] else []
                return PaymentPlan(**data)
            return None
    
    async def get_all_plans(self, active_only: bool = True) -> List[PaymentPlan]:
        """Get all payment plans"""
        async with self.get_connection() as conn:
            query = "SELECT * FROM payment_plans"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY price"
            
            cursor = await conn.execute(query)
            rows = await cursor.fetchall()
            plans = []
            for row in rows:
                data = dict(row)
                data['features'] = json.loads(data['features']) if data['features'] else []
                plans.append(PaymentPlan(**data))
            return plans
    
    async def update_plan(self, plan: PaymentPlan) -> PaymentPlan:
        """Update existing payment plan"""
        plan.updated_at = datetime.now()
        async with self.get_connection() as conn:
            features_json = json.dumps(plan.features)
            await conn.execute("""
                UPDATE payment_plans SET name = ?, duration_days = ?, price = ?, original_price = ?,
                                         features = ?, qr_code_file_id = ?, button_text = ?,
                                         is_active = ?, updated_at = ?
                WHERE plan_id = ?
            """, (
                plan.name, plan.duration_days, plan.price, plan.original_price,
                features_json, plan.qr_code_file_id, plan.button_text,
                plan.is_active, plan.updated_at, plan.plan_id
            ))
            await conn.commit()
            return plan
    
    async def delete_plan(self, plan_id: str) -> bool:
        """Delete payment plan (soft delete)"""
        async with self.get_connection() as conn:
            await conn.execute("UPDATE payment_plans SET is_active = 0 WHERE plan_id = ?", (plan_id,))
            await conn.commit()
            return True
    
    # =================== USER SESSION OPERATIONS ===================
    
    async def update_user_session(self, session: UserSession) -> UserSession:
        """Update or create user session"""
        session.last_activity = datetime.now()
        async with self.get_connection() as conn:
            session_data_json = json.dumps(session.session_data)
            await conn.execute("""
                INSERT INTO user_sessions (user_id, current_menu_id, session_data, state, last_activity)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    current_menu_id = excluded.current_menu_id,
                    session_data = excluded.session_data,
                    state = excluded.state,
                    last_activity = excluded.last_activity
            """, (
                session.user_id, session.current_menu_id, session_data_json,
                session.state, session.last_activity
            ))
            await conn.commit()
            return session
    
    async def get_user_session(self, user_id: int) -> Optional[UserSession]:
        """Get user session"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM user_sessions WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            if row:
                data = dict(row)
                data['session_data'] = json.loads(data['session_data']) if data['session_data'] else {}
                return UserSession(**data)
            return None
    
    # =================== USER OPERATIONS ===================
    
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, coins, referrer_id,
                                   total_referrals, total_earnings, is_banned, has_premium,
                                   premium_expires_at, created_at, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.user_id, user.username, user.first_name, user.last_name, user.coins,
                user.referrer_id, user.total_referrals, user.total_earnings, user.is_banned,
                user.has_premium, user.premium_expires_at, user.created_at, user.last_seen
            ))
            await conn.commit()
            return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            if row:
                return User(**dict(row))
            return None
    
    async def update_user(self, user: User) -> User:
        """Update existing user"""
        user.last_seen = datetime.now()
        async with self.get_connection() as conn:
            await conn.execute("""
                UPDATE users SET username = ?, first_name = ?, last_name = ?, coins = ?,
                                 referrer_id = ?, total_referrals = ?, total_earnings = ?,
                                 is_banned = ?, has_premium = ?, premium_expires_at = ?, last_seen = ?
                WHERE user_id = ?
            """, (
                user.username, user.first_name, user.last_name, user.coins, user.referrer_id,
                user.total_referrals, user.total_earnings, user.is_banned, user.has_premium,
                user.premium_expires_at, user.last_seen, user.user_id
            ))
            await conn.commit()
            return user
    
    async def get_or_create_user(self, user_id: int, username: str = None,
                                  first_name: str = None, last_name: str = None,
                                  referrer_id: int = None) -> User:
        """Get existing user or create new one"""
        user = await self.get_user(user_id)
        if user:
            # Update last_seen
            user.last_seen = datetime.now()
            await self.update_user(user)
            return user
        else:
            # Create new user
            new_user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                referrer_id=referrer_id
            )
            return await self.create_user(new_user)
    
    # =================== PAYMENT OPERATIONS ===================
    
    async def create_payment(self, payment: Payment) -> Payment:
        """Create a new payment record"""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO payments (payment_id, user_id, plan_id, amount, screenshot_file_id,
                                      status, admin_id, user_details, created_at, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                payment.payment_id, payment.user_id, payment.plan_id, payment.amount,
                payment.screenshot_file_id, payment.status.value, payment.admin_id,
                payment.user_details, payment.created_at, payment.processed_at
            ))
            await conn.commit()
            return payment
    
    async def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Get payment by ID"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
            row = await cursor.fetchone()
            if row:
                return Payment(**dict(row))
            return None
    
    async def update_payment(self, payment: Payment) -> Payment:
        """Update existing payment"""
        async with self.get_connection() as conn:
            await conn.execute("""
                UPDATE payments SET status = ?, admin_id = ?, user_details = ?, processed_at = ?
                WHERE payment_id = ?
            """, (
                payment.status.value, payment.admin_id, payment.user_details,
                payment.processed_at, payment.payment_id
            ))
            await conn.commit()
            return payment
    
    async def get_pending_payments(self) -> List[Payment]:
        """Get all pending payments"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT * FROM payments WHERE status = 'pending' ORDER BY created_at DESC
            """)
            rows = await cursor.fetchall()
            return [Payment(**dict(row)) for row in rows]
    
    # =================== ADMIN OPERATIONS ===================
    
    async def create_admin(self, admin: AdminUser) -> AdminUser:
        """Create admin user"""
        async with self.get_connection() as conn:
            permissions_json = json.dumps(admin.permissions)
            await conn.execute("""
                INSERT INTO admin_users (admin_id, role, permissions, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                admin.admin_id, admin.role.value, permissions_json, admin.is_active, admin.created_at
            ))
            await conn.commit()
            return admin
    
    async def get_admin(self, admin_id: int) -> Optional[AdminUser]:
        """Get admin by ID"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM admin_users WHERE admin_id = ? AND is_active = 1", (admin_id,))
            row = await cursor.fetchone()
            if row:
                data = dict(row)
                data['permissions'] = json.loads(data['permissions']) if data['permissions'] else {}
                return AdminUser(**data)
            return None
    
    async def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin"""
        admin = await self.get_admin(user_id)
        return admin is not None


# Global database instance
db = DatabaseManager()
