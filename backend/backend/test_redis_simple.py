#!/usr/bin/env python3
"""
Simple Redis connectivity test for Upstash
"""

import asyncio
import redis.asyncio as redis
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

async def test_upstash_redis():
    """Test Upstash Redis with different connection methods"""
    
    redis_url = os.environ.get('REDIS_URL')
    print(f"Testing Redis URL: {redis_url[:20]}...@upstash.io")
    
    # Method 1: Basic connection
    try:
        print("\n🔍 Method 1: Basic connection")
        client = redis.from_url(redis_url, decode_responses=True)
        result = await client.ping()
        print(f"✅ Ping successful: {result}")
        
        # Test set/get
        await client.set("test", "hello")
        value = await client.get("test")
        print(f"✅ Set/Get successful: {value}")
        
        await client.delete("test")
        await client.aclose()
        return True
        
    except Exception as e:
        print(f"❌ Method 1 failed: {str(e)}")
    
    # Method 2: Explicit SSL
    try:
        print("\n🔍 Method 2: Explicit SSL configuration")
        client = redis.from_url(
            redis_url, 
            decode_responses=True,
            ssl_cert_reqs=None,
            ssl_check_hostname=False,
            ssl_ca_certs=None
        )
        result = await client.ping()
        print(f"✅ SSL Ping successful: {result}")
        
        await client.set("test", "hello_ssl")
        value = await client.get("test")
        print(f"✅ SSL Set/Get successful: {value}")
        
        await client.delete("test")
        await client.aclose()
        return True
        
    except Exception as e:
        print(f"❌ Method 2 failed: {str(e)}")
    
    # Method 3: Manual URL parsing
    try:
        print("\n🔍 Method 3: Manual connection")
        from urllib.parse import urlparse
        parsed = urlparse(redis_url)
        
        client = redis.Redis(
            host=parsed.hostname,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password,
            decode_responses=True
        )
        result = await client.ping()
        print(f"✅ Manual Ping successful: {result}")
        
        await client.aclose()
        return True
        
    except Exception as e:
        print(f"❌ Method 3 failed: {str(e)}")
    
    return False

if __name__ == "__main__":
    asyncio.run(test_upstash_redis())