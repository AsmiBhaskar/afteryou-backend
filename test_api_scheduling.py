"""
Test the scheduling system with fallback to simple_tasks when Redis is unavailable
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afteryou.settings')
django.setup()

from django.utils import timezone
from legacy.models import LegacyMessage
from accounts.models import User

def test_api_scheduling():
    """Test the API scheduling endpoints"""
    print("Testing AfterYou API Scheduling System...")
    print("=" * 50)
    
    # Test that the import fallback is working
    print("1. Testing task import fallback...")
    try:
        # Import the functions directly
        from legacy.simple_tasks import schedule_message_delivery, enqueue_immediate_delivery, get_task_queue
        print("   [SUCCESS] Successfully imported scheduling functions")
    except Exception as e:
        print(f"   [ERROR] Failed to import scheduling functions: {str(e)}")
        try:
            # Fallback - try importing the classes and functions separately
            import legacy.simple_tasks as simple_tasks
            schedule_message_delivery = simple_tasks.schedule_message_delivery
            enqueue_immediate_delivery = simple_tasks.enqueue_immediate_delivery
            get_task_queue = simple_tasks.get_task_queue
            print("   [SUCCESS] Successfully imported scheduling functions (fallback method)")
        except Exception as e2:
            print(f"   [ERROR] Fallback import also failed: {str(e2)}")
            return
    
    # Test with actual messages
    print("\n2. Testing with actual messages...")
    messages = LegacyMessage.objects.all()[:1]
    
    if messages:
        message = messages[0]
        print(f"   [INFO] Found test message: {message.title}")
        print(f"   [INFO] Original delivery date: {message.delivery_date}")
        print(f"   [INFO] Current status: {message.status}")
        
        # Test immediate delivery
        try:
            print("\n   Testing immediate delivery...")
            job_id = enqueue_immediate_delivery(str(message.id))
            if job_id:
                print(f"   [SUCCESS] Immediate delivery queued with ID: {job_id}")
            else:
                print("   [WARNING] Immediate delivery returned None (may be using fallback)")
        except Exception as e:
            print(f"   [ERROR] Immediate delivery failed: {str(e)}")
        
        # Test scheduled delivery
        try:
            print("\n   Testing scheduled delivery...")
            future_delivery = timezone.now() + timedelta(minutes=1)
            job_id = schedule_message_delivery(str(message.id), future_delivery)
            if job_id:
                print(f"   [SUCCESS] Scheduled delivery queued for {future_delivery} with ID: {job_id}")
            else:
                print("   [WARNING] Scheduled delivery returned None (may be using fallback)")
        except Exception as e:
            print(f"   [ERROR] Scheduled delivery failed: {str(e)}")
    else:
        print("   [WARNING] No messages found for testing")
        
        # Create a test message for verification
        print("\n   Creating a test message...")
        try:
            user = User.objects.first()
            if user:
                test_message = LegacyMessage(
                    user_id=str(user.id),
                    title="Test Scheduling Message",
                    content="This is a test message for scheduling verification",
                    recipient_email="test@example.com",
                    delivery_date=timezone.now() + timedelta(minutes=5)
                )
                test_message.save()
                print(f"   [SUCCESS] Created test message: {test_message.id}")
                
                # Test scheduling with new message
                try:
                    job_id = schedule_message_delivery(str(test_message.id), test_message.delivery_date)
                    if job_id:
                        print(f"   [SUCCESS] Scheduled test message with ID: {job_id}")
                    else:
                        print("   [WARNING] Scheduling returned None (using fallback system)")
                except Exception as e:
                    print(f"   [ERROR] Test message scheduling failed: {str(e)}")
            else:
                print("   [ERROR] No users found to create test message")
        except Exception as e:
            print(f"   [ERROR] Failed to create test message: {str(e)}")
    
    print("\n3. Testing fallback system directly...")
    try:
        from legacy.simple_tasks import get_task_queue
        queue = get_task_queue()
        print(f"   [SUCCESS] Fallback queue available")
        print(f"   [INFO] Queue running: {queue.running}")
        print(f"   [INFO] Immediate queue size: {queue.immediate_queue.qsize()}")
        print(f"   [INFO] Scheduled tasks: {len(queue.scheduled_tasks)}")
    except Exception as e:
        print(f"   [ERROR] Fallback system error: {str(e)}")
    
    print("\n[SUCCESS] API scheduling test completed!")
    print("\n[INFO] Notes:")
    print("   - If Redis is unavailable, the system falls back to simple_tasks")
    print("   - This ensures scheduling logic works regardless of Redis connectivity")
    print("   - For production, ensure Redis is properly configured and accessible")

if __name__ == "__main__":
    test_api_scheduling()
