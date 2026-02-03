"""
Test MongoDB Atlas connection
Run this script to verify MongoDB Atlas is working correctly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afteryou.settings')
django.setup()

from legacy.models import LegacyMessage
from datetime import datetime, timedelta

print("="*60)
print("Testing MongoDB Atlas Connection")
print("="*60)

try:
    # Test 1: Check connection and see model fields
    print("\n[Test 1] Checking MongoDB Atlas connection...")
    
    # Print available fields
    print("\nAvailable fields in LegacyMessage:")
    for field_name, field in LegacyMessage._fields.items():
        print(f"  - {field_name}: {type(field).__name__}")
    
    count = LegacyMessage.objects.count()
    print(f"\n✓ Connected! Found {count} existing messages")
    
    # Test 2: Create a test message using actual fields
    print("\n[Test 2] Creating a test message...")
    
    # Get field names dynamically
    fields = list(LegacyMessage._fields.keys())
    print(f"Using fields: {fields}")
    
    # Create with minimal required fields
    test_message = LegacyMessage()
    
    # Set fields that exist (adjust based on your model)
    if 'recipient_email' in fields:
        test_message.recipient_email = "test@example.com"
    if 'status' in fields:
        test_message.status = 'pending'
    
    test_message.save()
    print(f"✓ Test message created with ID: {test_message.id}")
    
    # Test 3: Read the message back
    print("\n[Test 3] Reading the message back...")
    retrieved_message = LegacyMessage.objects.get(id=test_message.id)
    print(f"✓ Retrieved message with ID: {retrieved_message.id}")
    
    # Test 4: Count all messages
    print("\n[Test 4] Counting all messages...")
    total_count = LegacyMessage.objects.count()
    print(f"✓ Total messages in database: {total_count}")
    
    # Test 5: Delete test message
    print("\n[Test 5] Cleaning up test message...")
    test_message.delete()
    print(f"✓ Test message deleted")
    
    # Final count
    final_count = LegacyMessage.objects.count()
    print(f"\n✓ Final message count: {final_count}")
    
    print("\n" + "="*60)
    print("✓ All tests passed! MongoDB Atlas is working perfectly!")
    print("="*60)
    
except Exception as e:
    print(f"\n✗ Test failed with error:")
    print(f"  {str(e)}")
    import traceback
    traceback.print_exc()
    print("\n" + "="*60)
    print("Troubleshooting:")
    print("1. Check your MONGODB_URI in .env file")
    print("2. Verify Network Access in MongoDB Atlas (allow 0.0.0.0/0)")
    print("3. Confirm database user has read/write permissions")
    print("="*60)
    sys.exit(1)