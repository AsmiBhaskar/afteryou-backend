import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afteryou.settings')
django.setup()

from celery import Celery
from django.conf import settings

print("="*60)
print("Testing Celery with Upstash Redis")
print("="*60)

try:
    # Initialize Celery
    app = Celery('afteryou')
    app.config_from_object('django.conf:settings', namespace='CELERY')
    
    print("\n✓ Celery app initialized")
    print(f"Broker: {settings.CELERY_BROKER_URL[:30]}...")
    print(f"Backend: {settings.CELERY_RESULT_BACKEND[:30]}...")
    
    # Test broker connection
    print("\nTesting broker connection...")
    conn = app.connection()
    conn.ensure_connection(max_retries=3)
    print("✓ Broker connection successful!")
    conn.release()
    
    print("\n" + "="*60)
    print("✓ Celery is configured correctly!")
    print("="*60)
    print("\nNext steps:")
    print("1. Start Celery worker: celery -A afteryou worker --loglevel=info --pool=solo")
    print("2. Start Celery beat: celery -A afteryou beat --loglevel=info")
    
except Exception as e:
    print(f"\n✗ Celery test failed!")
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)