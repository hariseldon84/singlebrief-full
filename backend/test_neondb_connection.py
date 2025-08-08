#!/usr/bin/env python3
"""
Test NeonDB connection script
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.database import engine, redis_client
import structlog
from sqlalchemy import text

logger = structlog.get_logger(__name__)

async def test_database_connection():
    """Test PostgreSQL database connection"""
    print("🔍 Testing NeonDB PostgreSQL connection...")
    print(f"📋 Using DATABASE_URL: {settings.DATABASE_URL_COMPUTED}")
    
    try:
        # Test basic connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ PostgreSQL connected successfully!")
            print(f"📊 Database version: {version[0]}")
            
            # Test basic query
            result = await conn.execute(text("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()"))
            db_info = result.fetchone()
            print(f"📋 Database: {db_info[0]}")
            print(f"👤 User: {db_info[1]}")
            print(f"🌐 Server: {db_info[2]}:{db_info[3]}")
            
            # Test table creation capability
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS connection_test (
                    id SERIAL PRIMARY KEY,
                    test_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ Table creation test passed")
            
            # Test insert/select
            await conn.execute(text("""
                INSERT INTO connection_test (test_message) 
                VALUES ('NeonDB connection test successful')
            """))
            
            result = await conn.execute(text("SELECT * FROM connection_test ORDER BY created_at DESC LIMIT 1"))
            test_row = result.fetchone()
            print(f"✅ Insert/Select test passed: {test_row[1]}")
            
            # Cleanup
            await conn.execute(text("DROP TABLE connection_test"))
            print("✅ Cleanup completed")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

async def test_redis_connection():
    """Test Redis connection"""
    print("\n🔍 Testing Redis connection...")
    print(f"📋 Using REDIS_URL: {settings.REDIS_URL}")
    
    try:
        # Test ping
        result = await redis_client.ping()
        if result:
            print("✅ Redis connected successfully!")
            
            # Test set/get
            await redis_client.set("test_key", "NeonDB integration test")
            value = await redis_client.get("test_key")
            print(f"✅ Redis set/get test passed: {value}")
            
            # Cleanup
            await redis_client.delete("test_key")
            print("✅ Redis cleanup completed")
            return True
        else:
            print("❌ Redis ping failed")
            return False
            
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        print("ℹ️  Note: Redis failure is expected if not running locally")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting SingleBrief Database Connection Tests")
    print("=" * 50)
    
    # Test database connection
    db_success = await test_database_connection()
    
    # Test Redis connection (non-blocking if fails)
    redis_success = await test_redis_connection()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"  PostgreSQL (NeonDB): {'✅ SUCCESS' if db_success else '❌ FAILED'}")
    print(f"  Redis: {'✅ SUCCESS' if redis_success else '❌ FAILED (expected if not running locally)'}")
    
    if db_success:
        print("\n🎉 NeonDB connection is working correctly!")
        print("   You can now run your application with confidence.")
    else:
        print("\n🚨 Database connection issues detected!")
        print("   Please check your .env configuration and NeonDB credentials.")
    
    # Close connections
    try:
        await engine.dispose()
        await redis_client.close()
    except:
        pass

if __name__ == "__main__":
    asyncio.run(main())