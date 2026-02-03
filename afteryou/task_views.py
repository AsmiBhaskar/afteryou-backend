"""
QStash Task Endpoints
These views receive HTTP requests from QStash and execute background tasks.
All endpoints must verify QStash signature for security.
"""
import json
import hashlib
import hmac
import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from decouple import config


def verify_qstash_signature(request):
    """
    Verify that the request came from QStash using signature validation.
    Returns True if signature is valid, False otherwise.
    """
    signature = request.headers.get('Upstash-Signature')
    if not signature:
        return False
    
    current_signing_key = config('QSTASH_CURRENT_SIGNING_KEY')
    next_signing_key = config('QSTASH_NEXT_SIGNING_KEY', default='')
    
    body = request.body
    
    # Try current signing key
    expected_sig = base64.b64encode(
        hmac.new(
            current_signing_key.encode(),
            body,
            hashlib.sha256
        ).digest()
    ).decode()
    
    if signature == expected_sig:
        return True
    
    # Try next signing key (for key rotation)
    if next_signing_key:
        expected_sig_next = base64.b64encode(
            hmac.new(
                next_signing_key.encode(),
                body,
                hashlib.sha256
            ).digest()
        ).decode()
        
        if signature == expected_sig_next:
            return True
    
    return False


@csrf_exempt
@require_http_methods(["POST"])
def send_check_in_reminders_task(request):
    """Task: Send check-in reminder emails to users."""
    if not verify_qstash_signature(request):
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    
    try:
        # Import here to avoid circular imports
        from accounts.tasks import send_check_in_reminders
        
        # Execute the task
        result = send_check_in_reminders()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Check-in reminders sent',
            'result': result
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def process_scheduled_messages_task(request):
    """Task: Process and send scheduled legacy messages."""
    if not verify_qstash_signature(request):
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    
    try:
        # Import here to avoid circular imports
        from legacy.tasks import process_scheduled_messages
        
        # Execute the task
        result = process_scheduled_messages()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Scheduled messages processed',
            'result': result
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def send_final_warnings_task(request):
    """Task: Send final warning emails to inactive users."""
    if not verify_qstash_signature(request):
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    
    try:
        # Import here to avoid circular imports
        from accounts.tasks import send_final_warnings
        
        # Execute the task
        result = send_final_warnings()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Final warnings sent',
            'result': result
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def process_inactive_users_task(request):
    """Task: Process users who have been inactive beyond grace period."""
    if not verify_qstash_signature(request):
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    
    try:
        # Import here to avoid circular imports
        from accounts.tasks import process_inactive_users
        
        # Execute the task
        result = process_inactive_users()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Inactive users processed',
            'result': result
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def test_task(request):
    """Test endpoint to verify QStash integration."""
    if not verify_qstash_signature(request):
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    
    try:
        data = json.loads(request.body)
        message = data.get('message', 'No message provided')
        
        return JsonResponse({
            'status': 'success',
            'message': f'Test task received: {message}',
            'timestamp': str(request.META.get('HTTP_UPSTASH_MESSAGE_ID', 'unknown'))
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
