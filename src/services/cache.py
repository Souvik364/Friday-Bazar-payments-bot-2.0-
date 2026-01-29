"""
Friday Bazar Payments - Async Cache Layer
==========================================
In-memory cache with TTL for performance optimization
"""

import asyncio
import time
from typing import Any, Optional, Dict
from collections import OrderedDict


class AsyncCache:
    """Thread-safe async cache with TTL and LRU eviction"""
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        """
        Initialize cache
        
        Args:
            ttl_seconds: Time to live for cache entries (default 5 minutes)
            max_size: Maximum number of entries (LRU eviction)
        """
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            # Check if key exists
            if key not in self._cache:
                self._misses += 1
                return None
            
            # Check if expired
            if time.time() - self._timestamps[key] > self._ttl:
                # Expired - remove it
                del self._cache[key]
                del self._timestamps[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
    
    async def set(self, key: str, value: Any):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        async with self._lock:
            # If at max size, remove oldest entry (LRU)
            if len(self._cache) >= self._max_size and key not in self._cache:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                del self._timestamps[oldest_key]
            
            # Add/update entry
            self._cache[key] = value
            self._timestamps[key] = time.time()
            
            # Move to end (most recently used)
            if key in self._cache:
                self._cache.move_to_end(key)
    
    async def invalidate(self, key: str):
        """
        Remove entry from cache
        
        Args:
            key: Cache key to remove
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
    
    async def clear(self):
        """Clear entire cache"""
        async with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._hits = 0
            self._misses = 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.2f}%",
                "ttl_seconds": self._ttl
            }
    
    async def warm_up(self, data: Dict[str, Any]):
        """
        Pre-populate cache with data
        
        Args:
            data: Dictionary of key-value pairs to cache
        """
        for key, value in data.items():
            await self.set(key, value)


# Global cache instances
user_cache = AsyncCache(ttl_seconds=60, max_size=500)  # User data cache
service_cache = AsyncCache(ttl_seconds=300, max_size=100)  # Service catalog cache
order_cache = AsyncCache(ttl_seconds=120, max_size=300)  # Order cache
