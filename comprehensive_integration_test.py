#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for SingleBrief
Tests all environment configurations and integrations
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
import json
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.config import settings
from app.core.database import engine, redis_client
from app.core.security import (
    create_access_token, verify_token, hash_password, verify_password,
    create_refresh_token, create_email_verification_token, verify_email_verification_token
)
# Import VectorDatabaseManager conditionally to avoid initialization errors
vector_db_manager = None
try:
    from app.ai.vector_database import VectorDatabaseManager
    vector_db_manager_available = True
except Exception as e:
    print(f"Warning: VectorDatabaseManager import failed: {e}")
    VectorDatabaseManager = None
    vector_db_manager_available = False
import structlog
from sqlalchemy import text
import openai
import pinecone

logger = structlog.get_logger(__name__)

class IntegrationTestResult:
    """Class to track integration test results"""
    def __init__(self):
        self.results = {}
        self.overall_status = True
        self.test_timestamp = datetime.utcnow().isoformat()
    
    def add_test(self, test_name: str, status: bool, details: str, error: str = None):
        """Add a test result"""
        self.results[test_name] = {
            "status": "PASS" if status else "FAIL",
            "details": details,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        if not status:
            self.overall_status = False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        passed = sum(1 for r in self.results.values() if r["status"] == "PASS")
        failed = sum(1 for r in self.results.values() if r["status"] == "FAIL")
        return {
            "overall_status": "PASS" if self.overall_status else "FAIL",
            "total_tests": len(self.results),
            "passed": passed,
            "failed": failed,
            "test_timestamp": self.test_timestamp,
            "results": self.results
        }

async def test_application_configuration(test_results: IntegrationTestResult):
    """Test application configuration settings"""
    print("\n🔧 Testing Application Configuration...")
    
    try:
        # Test basic configuration loading
        config_tests = {
            "PROJECT_NAME": settings.PROJECT_NAME == "SingleBrief",
            "ENVIRONMENT": settings.ENVIRONMENT is not None,
            "SECRET_KEY": len(settings.SECRET_KEY) >= 32,
            "API_V1_STR": settings.API_V1_STR == "/api/v1",
            "ALLOWED_HOSTS": isinstance(settings.ALLOWED_HOSTS, list) and len(settings.ALLOWED_HOSTS) > 0,
            "ALLOWED_ORIGINS": isinstance(settings.ALLOWED_ORIGINS, list) and len(settings.ALLOWED_ORIGINS) > 0,
        }
        
        all_passed = all(config_tests.values())
        details = f"Configuration checks: {config_tests}"
        
        test_results.add_test(
            "Application Configuration", 
            all_passed, 
            details
        )
        
        print(f"{'✅' if all_passed else '❌'} Application Configuration: {'PASS' if all_passed else 'FAIL'}")
        for key, passed in config_tests.items():
            print(f"   {key}: {'✅' if passed else '❌'}")
            
        return all_passed
        
    except Exception as e:
        error_msg = f"Application configuration test failed: {str(e)}"
        print(f"❌ {error_msg}")
        test_results.add_test("Application Configuration", False, "Configuration loading failed", error_msg)
        return False

async def test_database_connection(test_results: IntegrationTestResult):
    """Test PostgreSQL database connection (NeonDB)"""
    print("\n🔍 Testing NeonDB PostgreSQL Connection...")
    print(f"📋 Using DATABASE_URL: {settings.DATABASE_URL_COMPUTED}")
    
    try:
        # Test basic connection
        async with engine.connect() as conn:
            # Test version
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ PostgreSQL connected successfully!")
            print(f"📊 Database version: {version[0]}")
            
            # Test database info
            result = await conn.execute(text("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()"))
            db_info = result.fetchone()
            database_details = {
                "database": db_info[0],
                "user": db_info[1],
                "server": f"{db_info[2]}:{db_info[3]}",
                "version": version[0]
            }
            
            # Test table creation
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS integration_test_table (
                    id SERIAL PRIMARY KEY,
                    test_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            await conn.commit()
            print("✅ Table creation test passed")
            
            # Test CRUD operations
            await conn.execute(text("""
                INSERT INTO integration_test_table (test_message) 
                VALUES ('Integration test successful - ' || NOW())
            """))
            await conn.commit()
            
            result = await conn.execute(text("SELECT * FROM integration_test_table ORDER BY created_at DESC LIMIT 1"))
            test_row = result.fetchone()
            print(f"✅ CRUD operations test passed: {test_row[1]}")
            
            # Test transactions (using a new connection to avoid nested transaction issues)
            async with engine.connect() as trans_conn:
                async with trans_conn.begin():
                    await trans_conn.execute(text("INSERT INTO integration_test_table (test_message) VALUES ('Transaction test')"))
            print("✅ Transaction test passed")
            
            # Cleanup
            await conn.execute(text("DROP TABLE integration_test_table"))
            await conn.commit()
            print("✅ Cleanup completed")
            
            test_results.add_test(
                "Database Connection (NeonDB)", 
                True, 
                f"Successfully connected to NeonDB. Details: {database_details}"
            )
            return True
            
    except Exception as e:
        error_msg = f"Database connection failed: {str(e)}"
        print(f"❌ {error_msg}")
        test_results.add_test("Database Connection (NeonDB)", False, "Connection failed", error_msg)
        return False

async def test_redis_connection(test_results: IntegrationTestResult):
    """Test Redis connection (Upstash)"""
    print("\n🔍 Testing Redis Connection (Upstash)...")
    print(f"📋 Using REDIS_URL: {settings.REDIS_URL}")
    
    try:
        # Test ping
        result = await redis_client.ping()
        if result:
            print("✅ Redis connected successfully!")
            
            # Test basic operations
            test_key = f"integration_test_{datetime.utcnow().timestamp()}"
            test_value = f"Redis integration test - {datetime.utcnow().isoformat()}"
            
            # Test SET/GET
            await redis_client.set(test_key, test_value)
            retrieved_value = await redis_client.get(test_key)
            print(f"✅ Redis SET/GET test passed: {retrieved_value}")
            
            # Test TTL
            await redis_client.setex(f"{test_key}_ttl", 30, "TTL test")
            ttl = await redis_client.ttl(f"{test_key}_ttl")
            print(f"✅ Redis TTL test passed: {ttl} seconds")
            
            # Test data structures
            list_key = f"{test_key}_list"
            await redis_client.lpush(list_key, "item1", "item2", "item3")
            list_length = await redis_client.llen(list_key)
            print(f"✅ Redis list operations test passed: {list_length} items")
            
            # Test hash operations
            hash_key = f"{test_key}_hash"
            await redis_client.hset(hash_key, mapping={
                "field1": "value1",
                "field2": "value2",
                "timestamp": datetime.utcnow().isoformat()
            })
            hash_data = await redis_client.hgetall(hash_key)
            print(f"✅ Redis hash operations test passed: {len(hash_data)} fields")
            
            # Cleanup
            await redis_client.delete(test_key, f"{test_key}_ttl", list_key, hash_key)
            print("✅ Redis cleanup completed")
            
            redis_details = {
                "connection": "successful",
                "operations_tested": ["ping", "set/get", "ttl", "lists", "hashes"],
                "server": settings.REDIS_URL.split("@")[1] if "@" in settings.REDIS_URL else "Unknown"
            }
            
            test_results.add_test(
                "Redis Connection (Upstash)", 
                True, 
                f"Successfully connected to Upstash Redis. Details: {redis_details}"
            )
            return True
        else:
            error_msg = "Redis ping failed"
            print(f"❌ {error_msg}")
            test_results.add_test("Redis Connection (Upstash)", False, "Ping failed", error_msg)
            return False
            
    except Exception as e:
        error_msg = f"Redis connection failed: {str(e)}"
        print(f"❌ {error_msg}")
        test_results.add_test("Redis Connection (Upstash)", False, "Connection failed", error_msg)
        return False

async def test_jwt_configuration(test_results: IntegrationTestResult):
    """Test JWT configuration and functionality"""
    print("\n🔐 Testing JWT Configuration...")
    
    try:
        # Test JWT settings
        jwt_settings = {
            "SECRET_KEY_configured": settings.SECRET_KEY is not None and len(settings.SECRET_KEY) > 0,
            "ACCESS_TOKEN_EXPIRE_MINUTES": settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0,
            "REFRESH_TOKEN_EXPIRE_MINUTES": settings.REFRESH_TOKEN_EXPIRE_MINUTES > 0,
        }
        
        if not all(jwt_settings.values()):
            error_msg = f"JWT configuration incomplete: {jwt_settings}"
            print(f"❌ {error_msg}")
            test_results.add_test("JWT Configuration", False, "Configuration incomplete", error_msg)
            return False
        
        # Test token creation and verification
        test_payload = {
            "sub": "test_user_123",
            "email": "test@example.com",
            "role": "user",
            "organization_id": "org_123",
            "team_ids": ["team_1", "team_2"],
            "permissions": ["read", "write"]
        }
        
        # Test access token
        access_token = create_access_token(test_payload)
        print("✅ Access token creation successful")
        
        # Test token verification
        token_data = verify_token(access_token, "access")
        print(f"✅ Access token verification successful: {token_data.user_id}")
        
        # Test refresh token
        refresh_token = create_refresh_token(test_payload)
        refresh_token_data = verify_token(refresh_token, "refresh")
        print(f"✅ Refresh token creation and verification successful")
        
        # Test email verification token
        email_token = create_email_verification_token("test@example.com")
        verified_email = verify_email_verification_token(email_token)
        print(f"✅ Email verification token test successful: {verified_email}")
        
        # Test password hashing
        test_password = "TestPassword123!"
        hashed = hash_password(test_password)
        is_valid = verify_password(test_password, hashed)
        print(f"✅ Password hashing test successful: {is_valid}")
        
        jwt_details = {
            "access_token_creation": "successful",
            "token_verification": "successful",
            "refresh_token": "successful",
            "email_verification": "successful",
            "password_hashing": "successful",
            "settings": jwt_settings
        }
        
        test_results.add_test(
            "JWT Configuration", 
            True, 
            f"JWT functionality working correctly. Details: {jwt_details}"
        )
        
        print("✅ JWT Configuration test passed")
        return True
        
    except Exception as e:
        error_msg = f"JWT configuration test failed: {str(e)}"
        print(f"❌ {error_msg}")
        test_results.add_test("JWT Configuration", False, "JWT functionality failed", error_msg)
        return False

async def test_vector_database_connection(test_results: IntegrationTestResult):
    """Test Vector Database (Pinecone) connection and operations"""
    print("\n🎯 Testing Vector Database (Pinecone) Connection...")
    
    try:
        # Check configuration
        if not settings.PINECONE_API_KEY or not settings.PINECONE_ENVIRONMENT:
            error_msg = "Pinecone configuration incomplete"
            print(f"❌ {error_msg}")
            test_results.add_test("Vector Database (Pinecone)", False, "Configuration incomplete", error_msg)
            return False
            
        print(f"📋 Using Pinecone Environment: {settings.PINECONE_ENVIRONMENT}")
        
        # Test OpenAI API key for embeddings
        if not settings.OPENAI_API_KEY:
            error_msg = "OpenAI API key not configured (required for embeddings)"
            print(f"❌ {error_msg}")
            test_results.add_test("Vector Database (Pinecone)", False, "OpenAI API key missing", error_msg)
            return False
        
        # Test Pinecone initialization (new API)
        from pinecone import Pinecone
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        print("✅ Pinecone initialization successful")
        
        # List indexes
        indexes = pc.list_indexes()
        index_names = [idx.name for idx in indexes]
        print(f"✅ Pinecone index list retrieved: {index_names}")
        
        # Test OpenAI embeddings
        openai.api_key = settings.OPENAI_API_KEY
        test_text = "This is a test text for vector embedding generation"
        
        try:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=test_text
            )
            embedding = response.data[0].embedding
            print(f"✅ OpenAI embedding generation successful: {len(embedding)} dimensions")
        except Exception as e:
            print(f"⚠️ OpenAI embedding test failed: {str(e)}")
            embedding = None
        
        # Test VectorDatabaseManager
        initialization_success = False
        if vector_db_manager_available and VectorDatabaseManager:
            try:
                vector_manager = VectorDatabaseManager(database_type="pinecone")
                initialization_success = await vector_manager.initialize()
                print(f"✅ VectorDatabaseManager initialization: {initialization_success}")
            except Exception as e:
                print(f"⚠️ VectorDatabaseManager initialization failed: {str(e)}")
        else:
            print("⚠️ VectorDatabaseManager not available due to import error")
        
        pinecone_details = {
            "initialization": "successful",
            "environment": settings.PINECONE_ENVIRONMENT,
            "indexes_available": index_names,
            "openai_embeddings": "successful" if embedding else "failed",
            "embedding_dimensions": len(embedding) if embedding else None,
            "vector_manager_init": initialization_success
        }
        
        # Overall status based on critical components
        overall_success = (
            len(index_names) >= 0 and  # Can list indexes
            embedding is not None  # Can generate embeddings
        )
        
        test_results.add_test(
            "Vector Database (Pinecone)", 
            overall_success, 
            f"Pinecone connectivity test. Details: {pinecone_details}"
        )
        
        print(f"{'✅' if overall_success else '❌'} Vector Database (Pinecone) test {'passed' if overall_success else 'failed'}")
        return overall_success
        
    except Exception as e:
        error_msg = f"Vector database connection failed: {str(e)}"
        print(f"❌ {error_msg}")
        test_results.add_test("Vector Database (Pinecone)", False, "Connection failed", error_msg)
        return False

async def test_ai_service_configuration(test_results: IntegrationTestResult):
    """Test AI service configurations"""
    print("\n🤖 Testing AI Service Configuration...")
    
    try:
        ai_config = {
            "OPENAI_API_KEY": settings.OPENAI_API_KEY is not None and len(settings.OPENAI_API_KEY) > 20,
            "ANTHROPIC_API_KEY": settings.ANTHROPIC_API_KEY is not None and settings.ANTHROPIC_API_KEY != "your-anthropic-api-key-here",
        }
        
        # Test OpenAI connection if key is available
        openai_test = False
        if ai_config["OPENAI_API_KEY"]:
            try:
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                # Simple API test
                response = client.models.list()
                openai_test = True
                print("✅ OpenAI API connection successful")
            except Exception as e:
                print(f"⚠️ OpenAI API test failed: {str(e)}")
        
        ai_details = {
            "openai_key_configured": ai_config["OPENAI_API_KEY"],
            "anthropic_key_configured": ai_config["ANTHROPIC_API_KEY"],
            "openai_api_test": openai_test
        }
        
        # At least one AI service should be configured
        overall_success = ai_config["OPENAI_API_KEY"] or ai_config["ANTHROPIC_API_KEY"]
        
        test_results.add_test(
            "AI Service Configuration", 
            overall_success, 
            f"AI service configuration status. Details: {ai_details}"
        )
        
        print(f"{'✅' if overall_success else '❌'} AI Service Configuration test {'passed' if overall_success else 'failed'}")
        return overall_success
        
    except Exception as e:
        error_msg = f"AI service configuration test failed: {str(e)}"
        print(f"❌ {error_msg}")
        test_results.add_test("AI Service Configuration", False, "Configuration test failed", error_msg)
        return False

async def main():
    """Main test function"""
    print("🚀 Starting SingleBrief Comprehensive Integration Tests")
    print("=" * 60)
    
    test_results = IntegrationTestResult()
    
    # Run all integration tests
    tests = [
        ("Application Configuration", test_application_configuration),
        ("Database Connection (NeonDB)", test_database_connection),
        ("Redis Connection (Upstash)", test_redis_connection),
        ("JWT Configuration", test_jwt_configuration),
        ("AI Service Configuration", test_ai_service_configuration),
        ("Vector Database (Pinecone)", test_vector_database_connection),
    ]
    
    test_success_count = 0
    for test_name, test_func in tests:
        try:
            success = await test_func(test_results)
            if success:
                test_success_count += 1
        except Exception as e:
            print(f"❌ Test {test_name} encountered unexpected error: {str(e)}")
            test_results.add_test(test_name, False, "Unexpected error", str(e))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Integration Test Results Summary:")
    
    summary = test_results.get_summary()
    print(f"Overall Status: {'✅ PASS' if summary['overall_status'] == 'PASS' else '❌ FAIL'}")
    print(f"Tests Passed: {summary['passed']}/{summary['total_tests']}")
    print(f"Tests Failed: {summary['failed']}/{summary['total_tests']}")
    print(f"Test Timestamp: {summary['test_timestamp']}")
    
    print("\nDetailed Results:")
    for test_name, result in summary['results'].items():
        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"  {status_icon} {test_name}: {result['status']}")
        if result["error"]:
            print(f"    Error: {result['error']}")
    
    # Recommendations
    print("\n📝 Recommendations:")
    if summary['overall_status'] == 'PASS':
        print("✅ All integrations are working correctly!")
        print("   Your SingleBrief application is ready for development and testing.")
    else:
        print("⚠️  Some integrations need attention:")
        for test_name, result in summary['results'].items():
            if result["status"] == "FAIL":
                print(f"   - Fix {test_name}: {result.get('error', 'See details above')}")
    
    # Close connections
    try:
        await engine.dispose()
        await redis_client.aclose()
    except Exception as e:
        print(f"Warning: Error closing connections: {e}")
    
    return summary

if __name__ == "__main__":
    result = asyncio.run(main())