"""
Friday Bazar Payments - JSON Database Manager
==============================================
Async JSON-based database for storing:
- User balances (Friday Coins)
- Referral mappings
- Order history

Optimized with caching layer for better performance
"""

import json
import aiofiles
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_dir: str = "data"):
        self.db_dir = Path(db_dir)
        self.users_file = self.db_dir / "users.json"
        self.orders_file = self.db_dir / "orders.json"
        self._lock = asyncio.Lock()
        
        # In-memory data storage
        self._users: Dict[str, Dict] = {}
        self._orders: List[Dict] = []
        
        # Persistence control
        self._users_dirty = False
        self._orders_dirty = False
        self._persistence_task = None
        self._running = False
        
    async def initialize(self):
        """Load data into memory and start persistence loop"""
        self.db_dir.mkdir(exist_ok=True)
        
        # Load Users
        if not self.users_file.exists():
            await self._write_file(self.users_file, {})
            self._users = {}
        else:
            self._users = await self._read_file(self.users_file)
            
        # Load Orders
        if not self.orders_file.exists():
            await self._write_file(self.orders_file, [])
            self._orders = []
        else:
            self._orders = await self._read_file(self.orders_file)
            
        logger.info(f"[DB] Initialized with {len(self._users)} users and {len(self._orders)} orders")
        
        # Start background save loop
        self._running = True
        self._persistence_task = asyncio.create_task(self._persistence_loop())
    
    async def shutdown(self):
        """Stop persistence loop and save remaining data"""
        logger.info("[DB] Shutting down...")
        self._running = False
        if self._persistence_task:
            try:
                # Wait for running save to finish if any, but we want to force final save
                self._persistence_task.cancel()
                await self._persistence_task
            except asyncio.CancelledError:
                pass
        
        # Final save
        await self._save_dirty_data()
        logger.info("[DB] Shutdown complete")

    async def _persistence_loop(self):
        """Periodically save dirty data to disk"""
        while self._running:
            try:
                await asyncio.sleep(5)  # Auto-save every 5 seconds
                await self._save_dirty_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[DB] Persistence error: {e}")

    async def _save_dirty_data(self):
        """Save data if marked as dirty"""
        async with self._lock:
            if self._users_dirty:
                await self._write_file(self.users_file, self._users)
                self._users_dirty = False
                # logger.debug("[DB] Saved users")
            
            if self._orders_dirty:
                await self._write_file(self.orders_file, self._orders)
                self._orders_dirty = False
                # logger.debug("[DB] Saved orders")

    async def _read_file(self, filepath: Path) -> Any:
        """Read JSON file asynchronously with non-blocking deserialization"""
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                content = await f.read()
                if not content:
                    return {} if str(filepath).endswith('users.json') else []
                
                # Offload JSON parsing to thread pool
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, json.loads, content)
        except Exception as e:
            logger.error(f"[DB] Read error {filepath}: {e}")
            return {} if str(filepath).endswith('users.json') else []
    
    async def _write_file(self, filepath: Path, data: Any):
        """Write JSON file asynchronously with non-blocking serialization"""
        try:
            # Offload JSON parsing to thread pool
            loop = asyncio.get_running_loop()
            json_str = await loop.run_in_executor(None, lambda: json.dumps(data, indent=2, ensure_ascii=False))
            
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(json_str)
        except Exception as e:
            logger.error(f"[DB] Write error {filepath}: {e}")
    
    # ==================== USER OPERATIONS ====================
    
    async def get_user(self, user_id: int) -> Dict:
        """Get user data directly from memory (Fast)"""
        user_key = str(user_id)
        
        # Try returning from memory immediately first
        if user_key in self._users:
            return self._users[user_key]
        
        # Create new if not exists
        async with self._lock:
            # Check again inside lock
            if user_key in self._users:
                return self._users[user_key]
                
            new_user = {
                "user_id": user_id,
                "coins": 0.0,
                "total_referrals": 0,
                "total_earned": 0.0,
                "referred_by": None,
                "joined_at": datetime.now().isoformat(),
                "purchases": [],
                "language": "en",
                "email": None,
                "subscription_plan": None,
                "subscription_service": None,
                "subscription_expiry": None,
                "subscription_status": "none"
            }
            self._users[user_key] = new_user
            self._users_dirty = True
            return new_user
    
    async def update_user(self, user_id: int, updates: Dict):
        """Update user in memory"""
        async with self._lock:
            user_key = str(user_id)
            if user_key in self._users:
                self._users[user_key].update(updates)
                self._users_dirty = True
                
                # Invalidate cache if external cache layer exists (optional now since DB IS cache)
                # But we keep it for compatibility if other modules use it
                try:
                    from src.services.cache import user_cache
                    await user_cache.invalidate(f"user_{user_id}")
                except ImportError:
                    pass
                return True
            return False
    
    async def set_referrer(self, user_id: int, referrer_id: int):
        async with self._lock:
            user_key = str(user_id)
            if user_key in self._users and not self._users[user_key]["referred_by"]:
                self._users[user_key]["referred_by"] = referrer_id
                self._users_dirty = True
                return True
            return False
    
    async def add_coins(self, user_id: int, amount: float, reason: str = ""):
        async with self._lock:
            user_key = str(user_id)
            if user_key in self._users:
                self._users[user_key]["coins"] += amount
                self._users[user_key]["total_earned"] += amount
                self._users_dirty = True
                return True
            return False
    
    async def increment_referral_count(self, user_id: int):
        async with self._lock:
            user_key = str(user_id)
            if user_key in self._users:
                self._users[user_key]["total_referrals"] += 1
                self._users_dirty = True
                return True
            return False
    
    # ==================== ORDER OPERATIONS ====================
    
    async def create_order(self, order_data: Dict) -> str:
        """Create order in memory (Instant)"""
        async with self._lock:
            order_id = f"FBP{len(self._orders) + 1:06d}"
            order = {
                "order_id": order_id,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                **order_data
            }
            
            self._orders.append(order)
            self._orders_dirty = True
            
            # Auto-save immediately for orders to be safe, but async
            # or rely on 5s loop. For reliability, let's allow loop to handle,
            # but if it crashes before 5s, data loss. 
            # For "Professional", maybe trigger save immediately for orders?
            # Let's rely on loop for performance, but shutdown hook for safety.
            
            return order_id
    
    async def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order from memory"""
        # No lock needed for read if we accept slight staleness during update
        # But for correctness with list traversal, better safe or use Dict for orders too next time
        # Currently orders is a List.
        for order in self._orders:
            if order["order_id"] == order_id:
                return order
        return None
    
    async def update_order(self, order_id: str, updates: Dict):
        async with self._lock:
            for order in self._orders:
                if order["order_id"] == order_id:
                    order.update(updates)
                    self._orders_dirty = True
                    return True
            return False
    
    async def add_purchase_to_user(self, user_id: int, order_id: str, amount: float):
        async with self._lock:
            user_key = str(user_id)
            if user_key in self._users:
                self._users[user_key]["purchases"].append({
                    "order_id": order_id,
                    "amount": amount,
                    "date": datetime.now().isoformat()
                })
                self._users_dirty = True
                return True
            return False

# Global database instance
db = Database()
