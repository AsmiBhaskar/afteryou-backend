#!/usr/bin/env python
"""
Test script for Legacy Chain functionality
Run this after setting up the chain features
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append('d:/django projects/TWO/afteryou')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afteryou.settings')
django.setup()

from legacy.models import LegacyMessage
from accounts.models import User
from django.utils import timezone

def test_chain_creation():
    """Test creating a message chain"""
    print("🧪 Testing Legacy Chain Creation...")
    
    # Get or create a test user
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        print(f"✅ Created test user: {user.username}")
    
    # Create an original message
    original_message = LegacyMessage(
        user_id=str(user.id),
        title="My Legacy Message",
        content="This is a test legacy message that will start a chain.",
        recipient_email="recipient1@example.com",
        delivery_date=timezone.now(),
        status='created',
        generation=1  # Original message
    )
    original_message.save()
    print(f"✅ Created original message: {original_message.id}")
    print(f"   Chain ID: {original_message.chain_id}")
    print(f"   Access Token: {original_message.recipient_access_token}")
    
    # Simulate a recipient extending the chain
    chain_message = LegacyMessage(
        user_id=str(user.id),  # Same user for tracking
        title=f"Re: {original_message.title}",
        content="Thank you for this beautiful message. I'm adding my own thoughts...",
        recipient_email="recipient2@example.com",
        delivery_date=timezone.now(),
        sender_name="First Recipient",
        parent_message=original_message,
        chain_id=original_message.chain_id,
        generation=2,
        status='created'
    )
    chain_message.save()
    print(f"✅ Created chain message: {chain_message.id}")
    print(f"   Generation: {chain_message.generation}")
    print(f"   Parent: {chain_message.parent_message.id}")
    
    # Test chain retrieval
    chain_messages = LegacyMessage.objects.filter(
        chain_id=original_message.chain_id
    ).order_by('generation')
    
    print(f"\n📋 Chain Summary:")
    print(f"   Chain ID: {original_message.chain_id}")
    print(f"   Total Messages: {len(chain_messages)}")
    
    for msg in chain_messages:
        print(f"   Gen {msg.generation}: {msg.title} -> {msg.recipient_email}")
        if msg.sender_name:
            print(f"              Added by: {msg.sender_name}")
    
    print(f"\n🔗 Chain URLs:")
    print(f"   Original: http://localhost:8000/legacy/message/{original_message.recipient_access_token}/")
    print(f"   Chain: http://localhost:8000/legacy/message/{chain_message.recipient_access_token}/")
    
    return original_message, chain_message

def test_api_endpoints():
    """Test the API endpoints"""
    print(f"\n🌐 API Endpoints Available:")
    print(f"   View Message: GET /api/message/<token>/")
    print(f"   Extend Chain: POST /api/message/<token>/extend/")
    print(f"   View Chain: GET /api/message/<token>/chain/")
    print(f"   User Chains: GET /api/chains/ (authenticated)")

if __name__ == "__main__":
    print("🚀 Legacy Chain Test Script")
    print("=" * 50)
    
    try:
        original, chain = test_chain_creation()
        test_api_endpoints()
        
        print(f"\n✅ All tests completed successfully!")
        print(f"\n📝 Next Steps:")
        print(f"   1. Start your Django server: python manage.py runserver")
        print(f"   2. Visit: http://localhost:8000/legacy/message/{original.recipient_access_token}/")
        print(f"   3. Test the 'Add Your Message & Pass It Forward' feature")
        print(f"   4. View the full chain history")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
