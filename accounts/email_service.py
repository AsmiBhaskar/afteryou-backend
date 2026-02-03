from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags

class DeadMansSwitchEmailService:
    """Service for sending dead man's switch related emails"""
    
    @staticmethod
    def send_check_in_reminder(user):
        """Send reminder email to user to check in"""
        subject = f"AfterYou - Check-in Reminder for {user.first_name or user.username}"
        
        context = {
            'user': user,
            'check_in_url': f"{settings.FRONTEND_URL}/dashboard",
            'grace_period_days': user.grace_period_days,
        }
        
        # Render HTML email
        html_message = render_to_string('emails/check_in_reminder.html', context)
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Failed to send check-in reminder to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_final_warning(user):
        """Send final warning before message delivery begins"""
        subject = f"AfterYou - FINAL WARNING: Legacy Messages Will Be Delivered Soon"
        
        context = {
            'user': user,
            'check_in_url': f"{settings.FRONTEND_URL}/dashboard",
            'message_count': user.legacymessage_set.filter(status='scheduled').count(),
        }
        
        # Render HTML email
        html_message = render_to_string('emails/final_warning.html', context)
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Failed to send final warning to {user.email}: {str(e)}")
            return False
