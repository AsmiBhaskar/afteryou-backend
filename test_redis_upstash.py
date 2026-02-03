import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afteryou.settings')
django.setup()

import redis
from django.conf import settings

print("="*60)
print("Testing Upstash Redis Connection")
print("="*60)

try:
    print(f"\nRedis URL: {settings.REDIS_URL[:30]}...")
    print(f"Using SSL: {settings.REDIS_URL.startswith('rediss://')}\n")
    
    # Connect to Redis
    print("Attempting connection...")
    if settings.REDIS_URL.startswith('rediss://'):
        r = redis.from_url(
            settings.REDIS_URL,
            ssl_cert_reqs=None,
            decode_responses=True
        )
    else:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    # Test ping
    r.ping()
    print("✓ Successfully connected to Upstash Redis!")
    
    # Test set/get
    print("\nTesting operations...")
    r.set('test_key', 'Hello from Django!')
    value = r.get('test_key')
    print(f"✓ Set/Get test: '{value}'")
    
    # Test increment
    r.set('counter', 0)
    r.incr('counter')
    counter_value = r.get('counter')
    print(f"✓ Increment test: {counter_value}")
    
    # Test list operations
    r.lpush('test_list', 'item1', 'item2', 'item3')
    list_length = r.llen('test_list')
    print(f"✓ List operations: {list_length} items")
    
    # Clean up
    r.delete('test_key', 'counter', 'test_list')
    print("\n✓ Cleanup completed")
    
    print("\n" + "="*60)
    print("✓ Upstash Redis is working perfectly!")
    print("="*60)
    
except redis.ConnectionError as e:
    print(f"\n✗ Connection failed!")
    print(f"Error: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Check REDIS_URL in .env file")
    print("2. Verify Upstash Redis database is active")
    print("3. Check network/firewall settings")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ Test failed!")
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)