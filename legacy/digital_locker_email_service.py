from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

class DigitalLockerEmailService:
    """Email service for Digital Locker inheritance notifications"""
    
    @staticmethod
    def send_inheritance_notification(locker, otp_token):
        """Send inheritance notification with OTP to inheritor"""
        
        subject = f"🔐 Digital Legacy Access - {locker.user.get_full_name() or locker.user.username}"
        
        context = {
            'locker': locker,
            'deceased_name': locker.user.get_full_name() or locker.user.username,
            'inheritor_name': locker.inheritor_name,
            'otp_token': otp_token,
            'access_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')}/digital-locker/access/{locker.id}",
            # Use settings.FRONTEND_URL if available
            'access_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')}/digital-locker/access/{locker.id}",
            'expires_hours': locker.otp_valid_hours,
            'credential_count': locker.credentials.filter(is_active=True).count(),
        }
        
        try:
            # Render HTML email
            html_message = render_to_string('emails/digital_locker_inheritance.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[locker.inheritor_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Log the notification
            from .digital_locker_models import LockerAccessLog
            LockerAccessLog.objects.create(
                locker=locker,
                action='otp_sent',
                details=f"Inheritance notification sent to {locker.inheritor_email}"
            )
            
            logger.info(f"Inheritance notification sent to {locker.inheritor_email} for locker {locker.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send inheritance notification: {str(e)}")
            return False
    
    @staticmethod
    def send_access_confirmation(locker):
        """Send confirmation to locker owner that access was granted"""
        
        # This would typically be sent to a designated executor or backup email
        # For now, we'll just log it
        logger.info(f"Digital locker {locker.id} was accessed by inheritor on {locker.accessed_at}")
        
        from .digital_locker_models import LockerAccessLog
        LockerAccessLog.objects.create(
            locker=locker,
            action='access_granted',
            details=f"Inheritor successfully accessed vault"
        )
    
    @staticmethod
    def send_auto_deletion_warning(locker, days_remaining):
        """Warn about upcoming auto-deletion"""
        
        subject = f"⚠️ Digital Legacy Auto-Deletion Warning - {days_remaining} days remaining"
        
        context = {
            'locker': locker,
            'days_remaining': days_remaining,
        }
        
        try:
            # This could be sent to a backup email or logged
            logger.warning(f"Digital locker {locker.id} will auto-delete in {days_remaining} days")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send auto-deletion warning: {str(e)}")
            return False
