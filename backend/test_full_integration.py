#!/usr/bin/env python3
"""
Comprehensive integration test script for SingleBrief
Tests: NeonDB PostgreSQL, Upstash Redis, OpenAI API
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.database import engine, redis_client
import structlog
from sqlalchemy import text
import openai

logger = structlog.get_logger(__name__)

async def test_database_connection():
    """Test NeonDB PostgreSQL connection"""
    print("🔍 Testing NeonDB PostgreSQL connection...")
    print(f"📋 Using DATABASE_URL: {settings.DATABASE_URL_COMPUTED}")
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ PostgreSQL connected successfully!")
            print(f"📊 Database version: {version[0][:50]}...")
            
            # Test basic query
            result = await conn.execute(text("SELECT current_database(), current_user"))
            db_info = result.fetchone()
            print(f"📋 Database: {db_info[0]}")
            print(f"👤 User: {db_info[1]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

async def test_redis_connection():
    """Test Upstash Redis connection"""
    print("\n🔍 Testing Upstash Redis connection...")
    print(f"📋 Redis Host: {settings.REDIS_HOST}")
    print(f"📋 Using REDIS_URL: redis://***@{settings.REDIS_HOST}:6379")
    
    try:
        # Test ping
        result = await redis_client.ping()
        if result:
            print("✅ Redis connected successfully!")
            
            # Test basic operations
            test_key = "singlebrief:test:connection"
            test_value = {
                "message": "Redis integration test successful",
                "timestamp": "2024-08-07",
                "service": "SingleBrief"
            }
            
            # Test set (with JSON serialization)
            await redis_client.set(test_key, json.dumps(test_value), ex=300)  # 5 minutes expiry
            print("✅ Redis SET operation successful")
            
            # Test get
            stored_value = await redis_client.get(test_key)
            parsed_value = json.loads(stored_value)
            print(f"✅ Redis GET operation successful: {parsed_value['message']}")
            
            # Test hash operations (commonly used in SingleBrief)
            hash_key = "singlebrief:user:test"
            await redis_client.hset(hash_key, mapping={
                "name": "Test User",
                "role": "admin",
                "last_active": "2024-08-07"
            })
            await redis_client.expire(hash_key, 300)  # 5 minutes expiry
            print("✅ Redis HASH operations successful")
            
            # Test retrieval
            user_data = await redis_client.hgetall(hash_key)
            print(f"✅ Redis HASH retrieval: {user_data['name']} ({user_data['role']})")
            
            # Test list operations (for queues/tasks)
            queue_key = "singlebrief:queue:test"
            await redis_client.lpush(queue_key, json.dumps({"task": "test_task", "priority": "high"}))
            await redis_client.expire(queue_key, 300)
            queue_item = await redis_client.rpop(queue_key)
            if queue_item:
                task_data = json.loads(queue_item)
                print(f"✅ Redis QUEUE operations successful: {task_data['task']}")
            
            # Cleanup
            await redis_client.delete(test_key, hash_key, queue_key)
            print("✅ Redis cleanup completed")
            return True
        else:
            print("❌ Redis ping failed")
            return False
            
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        print("🔍 Debug info:")
        print(f"   Redis Host: {settings.REDIS_HOST}")
        print(f"   Redis Port: {settings.REDIS_PORT}")
        return False

def test_openai_integration():
    """Test OpenAI API integration with minimal token usage"""
    print("\n🔍 Testing OpenAI API integration...")
    
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
        print("⚠️  OpenAI API key not configured")
        return False
    
    try:
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Test with minimal token usage - simple completion
        print("📋 Testing with minimal prompt to conserve tokens...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Most cost-effective model
            messages=[
                {"role": "user", "content": "Say 'OK' if you can read this."}
            ],
            max_tokens=5,  # Minimal token usage
            temperature=0  # Deterministic response
        )
        
        if response.choices and response.choices[0].message:
            reply = response.choices[0].message.content.strip()
            print(f"✅ OpenAI API connected successfully!")
            print(f"📊 Response: {reply}")
            print(f"📊 Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")
            print(f"📊 Model: {response.model}")
            
            # Test a SingleBrief-specific query (slightly longer but still minimal)
            print("📋 Testing SingleBrief-specific capability...")
            response2 = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Summarize in 5 words: AI assistant for team management"}
                ],
                max_tokens=10,
                temperature=0
            )
            
            if response2.choices and response2.choices[0].message:
                summary = response2.choices[0].message.content.strip()
                print(f"✅ AI summarization test: {summary}")
                print(f"📊 Total tokens used: {response2.usage.total_tokens if response2.usage else 'N/A'}")
            
            return True
        else:
            print("❌ OpenAI API returned empty response")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API test failed: {str(e)}")
        if "rate_limit" in str(e).lower():
            print("ℹ️  Rate limit hit - this is normal for new accounts")
        elif "insufficient_quota" in str(e).lower():
            print("ℹ️  Quota exceeded - please check your OpenAI billing")
        elif "invalid" in str(e).lower():
            print("ℹ️  API key may be invalid - please verify your OpenAI key")
        return False

async def test_application_startup():
    """Test that main application components can start"""
    print("\n🔍 Testing application component initialization...")
    
    try:
        # Test settings loading
        print(f"✅ Settings loaded: {settings.PROJECT_NAME} v{settings.VERSION}")
        print(f"✅ Environment: {settings.ENVIRONMENT}")
        
        # Test that database models can be imported
        try:
            from app.models import user, auth
            print("✅ Database models imported successfully")
        except ImportError as e:
            print(f"⚠️  Some model imports failed: {str(e)}")
        
        # Test that API endpoints can be imported
        try:
            from app.api.v1.endpoints import users, auth as auth_endpoints
            print("✅ API endpoints imported successfully")
        except ImportError as e:
            print(f"⚠️  Some endpoint imports failed: {str(e)}")
        
        # Test that core services can be imported
        from app.services import brief_generation
        print("✅ Core services imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Application component test failed: {str(e)}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting SingleBrief Comprehensive Integration Tests")
    print("=" * 60)
    
    # Test database connection
    db_success = await test_database_connection()
    
    # Test Redis connection
    redis_success = await test_redis_connection()
    
    # Test OpenAI integration
    openai_success = test_openai_integration()
    
    # Test application startup
    app_success = await test_application_startup()
    
    print("\n" + "=" * 60)
    print("📊 Integration Test Results Summary:")
    print(f"  PostgreSQL (NeonDB):   {'✅ SUCCESS' if db_success else '❌ FAILED'}")
    print(f"  Redis (Upstash):       {'✅ SUCCESS' if redis_success else '❌ FAILED'}")
    print(f"  OpenAI API:            {'✅ SUCCESS' if openai_success else '❌ FAILED'}")
    print(f"  Application Startup:   {'✅ SUCCESS' if app_success else '❌ FAILED'}")
    
    # Overall status
    all_critical = db_success and redis_success and openai_success
    
    print(f"\n{'🎉' if all_critical else '⚠️ '} Overall Status: {'ALL SYSTEMS READY' if all_critical else 'SOME ISSUES DETECTED'}")
    
    if all_critical:
        print("   🚀 Your SingleBrief application is fully configured and ready to run!")
        print("   📋 Next steps:")
        print("      1. Run database migrations: alembic upgrade head")
        print("      2. Start the application: uvicorn main:app --reload")
        print("      3. Access the API docs: http://localhost:8000/docs")
    else:
        print("   🔧 Please address the failed integrations before proceeding.")
    
    # Close connections
    try:
        await engine.dispose()
        await redis_client.aclose()  # Use aclose() instead of deprecated close()
    except Exception as e:
        print(f"⚠️  Connection cleanup warning: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())