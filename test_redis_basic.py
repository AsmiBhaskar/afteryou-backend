"""
Basic Redis connectivity test
"""
import redis
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afteryou.settings')
django.setup()

def test_redis_basic():
    """Test basic Redis connectivity"""
    print("Testing Basic Redis Connection...")
    print("=" * 40)
    
    try:
        # Test 1: Direct Redis connection
        print("1. Testing direct redis-py connection...")
        r = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True, 
                       socket_connect_timeout=10, socket_timeout=10)
        
        # Test ping
        response = r.ping()
        print(f"   ✅ Ping response: {response}")
        
        # Test set/get
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        print(f"   ✅ Set/Get test: {value}")
        
        # Clean up
        r.delete('test_key')
        print("   ✅ Cleanup successful")
        
    except Exception as e:
        print(f"   ❌ Direct Redis connection failed: {str(e)}")
        return False
    
    try:
        # Test 2: Django-RQ connection
        print("\n2. Testing Django-RQ connection...")
        import django_rq
        
        # Get connection through django-rq
        connection = django_rq.get_connection('default')
        response = connection.ping()
        print(f"   ✅ Django-RQ ping response: {response}")
        
        # Test queue creation
        queue = django_rq.get_queue('default')
        print(f"   ✅ Queue created: {queue}")
        print(f"   📊 Queue length: {len(queue)}")
        
    except Exception as e:
        print(f"   ❌ Django-RQ connection failed: {str(e)}")
        return False
    
    try:
        # Test 3: Simple job enqueue
        print("\n3. Testing simple job enqueue...")
        
        def simple_test_job():
            return "Hello from Redis job!"
        
        job = queue.enqueue(simple_test_job)
        print(f"   ✅ Job enqueued: {job.id}")
        print(f"   🔄 Job status: {job.get_status()}")
        
        # Try to process the job immediately
        import time
        time.sleep(1)
        print(f"   🔄 Job status after 1s: {job.get_status()}")
        
    except Exception as e:
        print(f"   ❌ Job enqueue failed: {str(e)}")
        return False
    
    print("\n✅ All Redis tests passed!")
    return True

if __name__ == "__main__":
    test_redis_basic()
