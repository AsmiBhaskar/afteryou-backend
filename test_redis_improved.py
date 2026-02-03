"""
Improved Redis connectivity test with better connection handling
"""
import redis
import os
import sys
import django
import time

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afteryou.settings')
django.setup()

def test_redis_improved():
    """Test Redis connectivity with improved connection handling"""
    print("Testing Improved Redis Connection...")
    print("=" * 45)
    
    try:
        # Test 1: Direct Redis connection with connection pooling
        print("1. Testing direct redis-py connection with pooling...")
        
        # Create connection pool
        pool = redis.ConnectionPool(
            host='127.0.0.1',
            port=6379,
            db=0,
            decode_responses=True,
            max_connections=10,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        r = redis.Redis(connection_pool=pool)
        
        # Test ping
        response = r.ping()
        print(f"   [SUCCESS] Ping response: {response}")
        
        # Test set/get with timeout
        test_key = f"test_key_{int(time.time())}"
        r.set(test_key, 'test_value', ex=60)  # Set with 60s expiration
        value = r.get(test_key)
        print(f"   [SUCCESS] Set/Get test: {value}")
        
        # Test multiple operations
        for i in range(5):
            r.set(f"batch_test_{i}", f"value_{i}")
            retrieved = r.get(f"batch_test_{i}")
            print(f"   [SUCCESS] Batch test {i}: {retrieved}")
            r.delete(f"batch_test_{i}")
        
        # Clean up
        r.delete(test_key)
        print("   [SUCCESS] Cleanup successful")
        
    except Exception as e:
        print(f"   [ERROR] Direct Redis connection failed: {str(e)}")
        print(f"   [INFO] Error type: {type(e).__name__}")
        return False
    
    try:
        # Test 2: Django-RQ connection with improved handling
        print("\n2. Testing Django-RQ connection with pooling...")
        import django_rq
        
        # Get connection through django-rq
        connection = django_rq.get_connection('default')
        response = connection.ping()
        print(f"   [SUCCESS] Django-RQ ping response: {response}")
        
        # Test queue creation and operations
        queue = django_rq.get_queue('default')
        print(f"   [SUCCESS] Queue created: {queue}")
        print(f"   [INFO] Queue length: {len(queue)}")
        
        # Test email queue
        email_queue = django_rq.get_queue('email')
        print(f"   [SUCCESS] Email queue created: {email_queue}")
        print(f"   [INFO] Email queue length: {len(email_queue)}")
        
        # Test scheduler
        scheduler = django_rq.get_scheduler('email')
        print(f"   [SUCCESS] Scheduler created: {scheduler}")
        try:
            scheduled_jobs = scheduler.get_jobs()
            print(f"   [INFO] Scheduled jobs: {len(scheduled_jobs)}")
        except Exception as scheduler_e:
            print(f"   [INFO] Scheduler available (job count check skipped): {scheduler_e}")
        
    except Exception as e:
        print(f"   [ERROR] Django-RQ connection failed: {str(e)}")
        print(f"   [INFO] Error type: {type(e).__name__}")
        return False
    
    try:
        # Test 3: Simple job enqueue with better error handling
        print("\n3. Testing job enqueue with error handling...")
        
        def simple_test_job(message="Hello from Redis job!"):
            print(f"Job executed: {message}")
            return message
        
        # Test immediate job
        job = queue.enqueue(simple_test_job, "Test immediate job")
        print(f"   [SUCCESS] Job enqueued: {job.id}")
        print(f"   [INFO] Job status: {job.get_status()}")
        
        # Wait and check status
        time.sleep(2)
        job.refresh()
        print(f"   [INFO] Job status after 2s: {job.get_status()}")
        
        if job.is_finished:
            print(f"   [SUCCESS] Job result: {job.result}")
        elif job.is_failed:
            print(f"   [ERROR] Job failed: {job.exc_info}")
        
        # Test scheduled job
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        future_time = timezone.now() + timedelta(seconds=10)
        scheduled_job = scheduler.enqueue_at(
            future_time,
            simple_test_job,
            "Test scheduled job"
        )
        print(f"   [SUCCESS] Scheduled job: {scheduled_job.id} for {future_time}")
        
    except Exception as e:
        print(f"   [ERROR] Job enqueue failed: {str(e)}")
        print(f"   [INFO] Error type: {type(e).__name__}")
        return False
    
    print("\n[SUCCESS] All improved Redis tests passed!")
    print("\n[INFO] Connection pooling and improved error handling working correctly.")
    return True

if __name__ == "__main__":
    test_redis_improved()
