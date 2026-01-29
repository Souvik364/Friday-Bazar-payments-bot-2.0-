"""
Performance Testing for Friday Bazar Payments Bot
==================================================
Test script to verify optimization goals are met

Run with: python tests/test_performance.py

Success Criteria:
- Callback response: < 200ms
- QR generation: < 1000ms
- Database operations: < 100ms
"""

import asyncio
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.db import db
from src.utils.helpers import generate_upi_qr_async  
from src.services.cache import user_cache, service_cache


async def test_database_read():
    """Test database read performance"""
    print("\n[TEST] Database Read Performance...")
    
    # Initialize database
    await db.initialize()
    
    # Test user read (with cache)
    start = time.time()
    user = await db.get_user(12345)
    elapsed_ms = (time.time() - start) * 1000
    
    status = "[PASS]" if elapsed_ms < 100 else "[FAIL]"
    print(f"   {status} User read (cold): {elapsed_ms:.2f}ms (target: <100ms)")
    
    # Test cached read (should be faster)
    start = time.time()
    user = await db.get_user(12345)
    elapsed_ms = (time.time() - start) * 1000
    
    status = "[PASS]" if elapsed_ms < 50 else "[FAIL]"
    print(f"   {status} User read (cached): {elapsed_ms:.2f}ms (target: <50ms)")
    
    return True


async def test_qr_generation():
    """Test QR code generation performance"""
    print("\n[TEST] QR Code Generation...")
    
    # Test async QR generation
    start = time.time()
    qr_image = await generate_upi_qr_async("test@upi", "Test", 100, "TEST123")
    elapsed_ms = (time.time() - start) * 1000
    
    status = "[PASS]" if elapsed_ms < 1000 else "[FAIL]"
    print(f"   {status} QR generation (first): {elapsed_ms:.2f}ms (target: <1000ms)")
    
    # Test cached QR generation (should be instant)
    start = time.time()
    qr_image = await generate_upi_qr_async("test@upi", "Test", 100, "TEST124")
    elapsed_ms = (time.time() - start) * 1000
    
    status = "[PASS]" if elapsed_ms < 100 else "[FAIL]"
    print(f"   {status} QR generation (cached): {elapsed_ms:.2f}ms (target: <100ms)")
    
    return True


async def test_cache_performance():
    """Test cache hit/miss performance"""
    print("\n[TEST] Cache Performance...")
    
    # Test cache write
    start = time.time()
    await service_cache.set("test_key", {"name": "Test Service"})
    elapsed_ms = (time.time() - start) * 1000
    print(f"   [OK] Cache write: {elapsed_ms:.2f}ms")
    
    # Test cache read (should be very fast)
    start = time.time()
    cached_value = await service_cache.get("test_key")
    elapsed_ms = ( - start) * 1000
    
    status = "[PASS]" if elapsed_ms < 10 else "[FAIL]"
    print(f"   {status} Cache read: {elapsed_ms:.2f}ms (target: <10ms)")
    
    # Test cache stats
    stats = await service_cache.get_stats()
    print(f"   [INFO] Cache stats: {stats}")
    
    return True


async def test_concurrent_operations():
    """Test concurrent database operations"""
    print("\n[TEST] Concurrent Operations...")
    
    async def simulate_user_operation(user_id):
        """Simulate a user operation"""
        user = await db.get_user(user_id)
        return user
    
    # Run 20 concurrent user fetches
    start = time.time()
    tasks = [simulate_user_operation(i) for i in range(20)]
    results = await asyncio.gather(*tasks)
    elapsed_ms = (time.time() - start) * 1000
    
    avg_per_user = elapsed_ms / 20
    status = "[PASS]" if avg_per_user < 50 else "[FAIL]"
    print(f"   {status} 20 concurrent user fetches: {elapsed_ms:.2f}ms total")
    print(f"   [INFO] Average per user: {avg_per_user:.2f}ms (target: <50ms)")
    
    return True


async def run_all_tests():
    """Run all performance tests"""
    print("="*60)
    print(" FRIDAY BAZAR PAYMENTS BOT - PERFORMANCE TEST SUITE")
    print("="*60)
    
    try:
        await test_database_read()
        await test_qr_generation()
        await test_cache_performance()
        await test_concurrent_operations()
        
        print("\n" + "="*60)
        print(" [SUCCESS] ALL TESTS COMPLETED")
        print("="*60)
        print("\n[NOTE] Run this on your production environment for accurate results.")
        print("   Render free tier may have slower performance than local testing.\n")
        
    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())
