from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from .digital_locker_models import DigitalLocker, CredentialEntry, LockerAccessToken, LockerAccessLog
import json
import logging

logger = logging.getLogger(__name__)

class DigitalLockerView(View):
    """Main view for managing digital locker"""
    
    @method_decorator(login_required)
    def get(self, request):
        """Get user's digital locker or create if doesn't exist"""
        try:
            locker = DigitalLocker.objects.get(user=request.user)
        except DigitalLocker.DoesNotExist:
            # Create default locker
            locker = DigitalLocker.objects.create(
                user=request.user,
                inheritor_name="",
                inheritor_email="",
                title=f"{request.user.get_full_name() or request.user.username}'s Digital Legacy Vault"
            )
            locker.generate_master_key()
            locker.save()
        
        # Get credentials summary
        credentials = locker.credentials.filter(is_active=True)
        credentials_by_category = {}
        for cred in credentials:
            category = cred.get_category_display()
            if category not in credentials_by_category:
                credentials_by_category[category] = []
            credentials_by_category[category].append({
                'id': cred.id,
                'title': cred.title,
                'account_identifier': cred.account_identifier,
                'website_url': cred.website_url,
                'priority': cred.priority,
                'updated_at': cred.updated_at.isoformat(),
            })
        
        return JsonResponse({
            'locker': {
                'id': locker.id,
                'title': locker.title,
                'description': locker.description,
                'status': locker.status,
                'inheritor_name': locker.inheritor_name,
                'inheritor_email': locker.inheritor_email,
                'inheritor_phone': locker.inheritor_phone,
                'otp_valid_hours': locker.otp_valid_hours,
                'access_attempts_limit': locker.access_attempts_limit,
                'auto_delete_after_access': locker.auto_delete_after_access,
                'auto_delete_days': locker.auto_delete_days,
                'created_at': locker.created_at.isoformat(),
                'triggered_at': locker.triggered_at.isoformat() if locker.triggered_at else None,
            },
            'credentials_count': credentials.count(),
            'credentials_by_category': credentials_by_category,
        })
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def put(self, request):
        """Update digital locker settings"""
        try:
            data = json.loads(request.body)
            locker = get_object_or_404(DigitalLocker, user=request.user)
            
            # Update allowed fields
            if 'title' in data:
                locker.title = data['title']
            if 'description' in data:
                locker.description = data['description']
            if 'inheritor_name' in data:
                locker.inheritor_name = data['inheritor_name']
            if 'inheritor_email' in data:
                locker.inheritor_email = data['inheritor_email']
            if 'inheritor_phone' in data:
                locker.inheritor_phone = data['inheritor_phone']
            if 'otp_valid_hours' in data:
                locker.otp_valid_hours = int(data['otp_valid_hours'])
            if 'access_attempts_limit' in data:
                locker.access_attempts_limit = int(data['access_attempts_limit'])
            if 'auto_delete_after_access' in data:
                locker.auto_delete_after_access = bool(data['auto_delete_after_access'])
            if 'auto_delete_days' in data:
                locker.auto_delete_days = int(data['auto_delete_days'])
            
            locker.save()
            
            # Log the update
            LockerAccessLog.objects.create(
                locker=locker,
                action='updated',
                ip_address=self.get_client_ip(request),
                details='Locker settings updated'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Digital locker updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error updating digital locker: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class CredentialView(View):
    """View for managing individual credentials"""
    
    @method_decorator(login_required)
    def get(self, request, credential_id=None):
        """Get credential details or list all credentials"""
        locker = get_object_or_404(DigitalLocker, user=request.user)
        
        if credential_id:
            # Get specific credential (without decrypted data for security)
            credential = get_object_or_404(CredentialEntry, id=credential_id, locker=locker)
            return JsonResponse({
                'id': credential.id,
                'title': credential.title,
                'category': credential.category,
                'website_url': credential.website_url,
                'account_identifier': credential.account_identifier,
                'notes': credential.notes,
                'priority': credential.priority,
                'is_active': credential.is_active,
                'created_at': credential.created_at.isoformat(),
                'updated_at': credential.updated_at.isoformat(),
            })
        else:
            # List all credentials
            credentials = locker.credentials.filter(is_active=True).order_by('priority', '-updated_at')
            return JsonResponse({
                'credentials': [
                    {
                        'id': cred.id,
                        'title': cred.title,
                        'category': cred.category,
                        'category_display': cred.get_category_display(),
                        'website_url': cred.website_url,
                        'account_identifier': cred.account_identifier,
                        'priority': cred.priority,
                        'updated_at': cred.updated_at.isoformat(),
                    }
                    for cred in credentials
                ]
            })
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Create new credential"""
        try:
            data = json.loads(request.body)
            locker = get_object_or_404(DigitalLocker, user=request.user)
            
            if locker.status != 'active':
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot add credentials to a locked vault'
                }, status=400)
            
            credential = CredentialEntry.objects.create(
                locker=locker,
                title=data.get('title', ''),
                category=data.get('category', 'other'),
                website_url=data.get('website_url', ''),
                account_identifier=data.get('account_identifier', ''),
                notes=data.get('notes', ''),
                priority=data.get('priority', 1),
            )
            
            # Set encrypted fields
            if 'username' in data:
                credential.set_username(data['username'])
            if 'password' in data:
                credential.set_password(data['password'])
            if 'additional_data' in data:
                credential.set_additional_data(data['additional_data'])
            
            credential.save()
            
            # Log the creation
            LockerAccessLog.objects.create(
                locker=locker,
                action='updated',
                ip_address=self.get_client_ip(request),
                details=f'Added credential: {credential.title}'
            )
            
            return JsonResponse({
                'success': True,
                'credential_id': credential.id,
                'message': 'Credential added successfully'
            })
            
        except Exception as e:
            logger.error(f"Error creating credential: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def put(self, request, credential_id):
        """Update existing credential"""
        try:
            data = json.loads(request.body)
            locker = get_object_or_404(DigitalLocker, user=request.user)
            credential = get_object_or_404(CredentialEntry, id=credential_id, locker=locker)
            
            if locker.status != 'active':
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot modify credentials in a locked vault'
                }, status=400)
            
            # Update fields
            if 'title' in data:
                credential.title = data['title']
            if 'category' in data:
                credential.category = data['category']
            if 'website_url' in data:
                credential.website_url = data['website_url']
            if 'account_identifier' in data:
                credential.account_identifier = data['account_identifier']
            if 'notes' in data:
                credential.notes = data['notes']
            if 'priority' in data:
                credential.priority = data['priority']
            if 'is_active' in data:
                credential.is_active = data['is_active']
            
            # Update encrypted fields
            if 'username' in data:
                credential.set_username(data['username'])
            if 'password' in data:
                credential.set_password(data['password'])
            if 'additional_data' in data:
                credential.set_additional_data(data['additional_data'])
            
            credential.save()
            
            # Log the update
            LockerAccessLog.objects.create(
                locker=locker,
                action='updated',
                ip_address=self.get_client_ip(request),
                details=f'Updated credential: {credential.title}'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Credential updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error updating credential: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def delete(self, request, credential_id):
        """Delete credential"""
        try:
            locker = get_object_or_404(DigitalLocker, user=request.user)
            credential = get_object_or_404(CredentialEntry, id=credential_id, locker=locker)
            
            if locker.status != 'active':
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot delete credentials from a locked vault'
                }, status=400)
            
            title = credential.title
            credential.delete()
            
            # Log the deletion
            LockerAccessLog.objects.create(
                locker=locker,
                action='updated',
                ip_address=self.get_client_ip(request),
                details=f'Deleted credential: {title}'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Credential deleted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error deleting credential: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class InheritanceAccessView(View):
    """View for inheritor access to digital locker"""
    
    @method_decorator(csrf_exempt)
    def post(self, request, locker_id):
        """Verify OTP and grant access to inheritor"""
        try:
            data = json.loads(request.body)
            otp_token = data.get('otp_token', '').strip()
            
            if not otp_token:
                return JsonResponse({
                    'success': False,
                    'error': 'OTP token is required'
                }, status=400)
            
            # Find the locker and access token
            locker = get_object_or_404(DigitalLocker, id=locker_id)
            access_token = get_object_or_404(LockerAccessToken, locker=locker, token=otp_token)
            
            if not access_token.is_valid():
                access_token.record_attempt()
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid or expired OTP token',
                    'attempts_remaining': locker.access_attempts_limit - access_token.attempts_used
                }, status=400)
            
            # Grant access
            if access_token.use_token():
                # Return decrypted credentials
                credentials = []
                for cred in locker.credentials.filter(is_active=True).order_by('priority', 'title'):
                    credentials.append({
                        'id': cred.id,
                        'title': cred.title,
                        'category': cred.get_category_display(),
                        'website_url': cred.website_url,
                        'account_identifier': cred.account_identifier,
                        'username': cred.get_username(),
                        'password': cred.get_password(),
                        'additional_data': cred.get_additional_data(),
                        'notes': cred.notes,
                        'priority': cred.priority,
                    })
                
                # Log access
                LockerAccessLog.objects.create(
                    locker=locker,
                    action='access_granted',
                    ip_address=self.get_client_ip(request),
                    details=f'Inheritor accessed vault with {len(credentials)} credentials'
                )
                
                # Send confirmation email
                from .digital_locker_email_service import DigitalLockerEmailService
                DigitalLockerEmailService.send_access_confirmation(locker)
                
                return JsonResponse({
                    'success': True,
                    'locker': {
                        'title': locker.title,
                        'description': locker.description,
                        'deceased_name': locker.user.get_full_name() or locker.user.username,
                        'accessed_at': locker.accessed_at.isoformat(),
                    },
                    'credentials': credentials,
                    'message': f'Access granted. {len(credentials)} credentials retrieved.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to grant access'
                }, status=500)
                
        except Exception as e:
            logger.error(f"Error granting inheritor access: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Access denied'
            }, status=500)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

@login_required
def trigger_inheritance(request):
    """Manually trigger inheritance process (for testing or emergency)"""
    if request.method == 'POST':
        try:
            locker = get_object_or_404(DigitalLocker, user=request.user)
            
            if not locker.inheritor_email:
                return JsonResponse({
                    'success': False,
                    'error': 'No inheritor email configured'
                }, status=400)
            
            if locker.status in ['triggered', 'accessed', 'expired']:
                return JsonResponse({
                    'success': False,
                    'error': f'Locker is already {locker.status}'
                }, status=400)
            
            # Trigger inheritance
            access_token = locker.trigger_inheritance()
            
            # Log the trigger
            LockerAccessLog.objects.create(
                locker=locker,
                action='triggered',
                ip_address=request.META.get('REMOTE_ADDR'),
                details='Inheritance manually triggered by user'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Inheritance triggered. OTP sent to {locker.inheritor_email}',
                'expires_at': access_token.expires_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error triggering inheritance: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
