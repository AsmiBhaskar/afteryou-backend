#!/usr/bin/env python
"""
Test the chain API endpoints directly
"""
import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append('d:/django projects/TWO/afteryou')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afteryou.settings')
django.setup()

from legacy.models import LegacyMessage

def test_api_endpoints():
    """Test API endpoints"""
    print("🌐 Testing Chain API Endpoints...")
    
    # Get the test message we created
    message = LegacyMessage.objects.first()
    if not message:
        print("❌ No test messages found. Run test_chain.py first.")
        return
    
    token = str(message.recipient_access_token)
    print(f"Testing with token: {token}")
    
    base_url = "http://localhost:8000"
    
    # Test 1: View message
    try:
        response = requests.get(f"{base_url}/api/message/{token}/")
        print(f"✅ View message: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Message title: {data['message']['title']}")
        else:
            print(f"   Error: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Server not running on localhost:8000")
        return
    except Exception as e:
        print(f"❌ View message failed: {e}")
    
    # Test 2: View chain
    try:
        response = requests.get(f"{base_url}/api/message/{token}/chain/")
        print(f"✅ View chain: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total generations: {data['total_generations']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ View chain failed: {e}")
    
    # Test 3: Extend chain
    try:
        extend_data = {
            "sender_name": "API Test User",
            "recipient_email": "apitest@example.com",
            "content": "This is a test extension via API."
        }
        response = requests.post(
            f"{base_url}/api/message/{token}/extend/",
            json=extend_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"✅ Extend chain: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   New generation: {data['chain_generation']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Extend chain failed: {e}")

if __name__ == "__main__":
    test_api_endpoints()
