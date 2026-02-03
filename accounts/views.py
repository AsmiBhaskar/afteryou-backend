from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.views.decorators.http import require_http_methods
from datetime import timedelta
from .forms import RegisterForm, LoginForm

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('legacy:dashboard')  # Redirect to dashboard
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('legacy:dashboard')  # Redirect to dashboard
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('accounts:login')  # Redirect to login page

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def check_in_view(request):
    """API endpoint for users to check in and reset their dead man's switch timer"""
    try:
        user = request.user
        user.last_check_in = now()
        user.notification_sent_at = None  # Reset notification status
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Check-in successful! Your timer has been reset.',
            'last_check_in': user.last_check_in.isoformat(),
            'next_check_in_due': (now() + timedelta(days=30 * user.check_in_interval_months)).isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def check_in_status_view(request):
    """Get user's current check-in status"""
    user = request.user
    current_time = now()
    
    # Calculate when user should check in next
    months_in_days = 30 * user.check_in_interval_months
    next_check_in_due = user.last_check_in + timedelta(days=months_in_days)
    
    # Calculate if user is overdue
    is_overdue = current_time > next_check_in_due
    
    # Check if in grace period
    in_grace_period = False
    grace_period_end = None
    if user.notification_sent_at:
        grace_period_end = user.notification_sent_at + timedelta(days=user.grace_period_days)
        in_grace_period = current_time < grace_period_end
    
    return JsonResponse({
        'last_check_in': user.last_check_in.isoformat(),
        'next_check_in_due': next_check_in_due.isoformat(),
        'check_in_interval_months': user.check_in_interval_months,
        'grace_period_days': user.grace_period_days,
        'is_overdue': is_overdue,
        'notification_sent_at': user.notification_sent_at.isoformat() if user.notification_sent_at else None,
        'in_grace_period': in_grace_period,
        'grace_period_end': grace_period_end.isoformat() if grace_period_end else None,
        'scheduled_messages_count': user.legacymessage_set.filter(status='scheduled').count()
    })

@login_required
@csrf_exempt
def update_user_settings_view(request):
    """Update user's dead man's switch settings"""
    if request.method == 'PUT':
        try:
            import json
            data = json.loads(request.body)
            user = request.user
            
            # Update settings
            if 'check_in_interval_months' in data:
                interval = int(data['check_in_interval_months'])
                if 1 <= interval <= 24:  # Validate range
                    user.check_in_interval_months = interval
            
            if 'grace_period_days' in data:
                grace_days = int(data['grace_period_days'])
                if 1 <= grace_days <= 30:  # Validate range
                    user.grace_period_days = grace_days
            
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Settings updated successfully',
                'check_in_interval_months': user.check_in_interval_months,
                'grace_period_days': user.grace_period_days
            })
            
        except (ValueError, json.JSONDecodeError) as e:
            return JsonResponse({
                'success': False,
                'error': 'Invalid data format'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

