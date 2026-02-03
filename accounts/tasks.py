from celery import shared_task
from django.core.management import call_command
from django.utils.timezone import now
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_dead_mans_switch():
    """
    Celery task to check for inactive users and trigger dead man's switch logic.
    This task runs daily and handles both notifications and message delivery.
    """
    try:
        logger.info("Starting dead man's switch check...")
        
        # Call the management command with email sending enabled
        call_command('trigger_inactive_users', '--send-emails')
        
        logger.info("Dead man's switch check completed successfully")
        return "Dead man's switch check completed"
        
    except Exception as e:
        logger.error(f"Error in dead man's switch check: {str(e)}")
        raise

@shared_task
def send_check_in_reminder(user_id):
    """
    Task to send a check-in reminder to a specific user.
    """
    from accounts.models import User
    from accounts.email_service import DeadMansSwitchEmailService
    
    try:
        user = User.objects.get(id=user_id)
        success = DeadMansSwitchEmailService.send_check_in_reminder(user)
        
        if success:
            # Update notification timestamp
            user.notification_sent_at = now()
            user.save()
            logger.info(f"Check-in reminder sent successfully to {user.email}")
        else:
            logger.error(f"Failed to send check-in reminder to {user.email}")
            
        return success
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending check-in reminder: {str(e)}")
        raise

@shared_task
def trigger_user_message_delivery(user_id):
    """
    Task to trigger message delivery for a specific user.
    """
    from accounts.models import User
    from legacy.models import LegacyMessage
    
    try:
        user = User.objects.get(id=user_id)
        messages = LegacyMessage.objects.filter(user=user, status='scheduled')
        
        if messages.exists():
            updated = messages.update(status='pending')
            
            # Reset user's notification status for future cycles
            user.notification_sent_at = None
            user.save()
            
            logger.info(f"Triggered delivery of {updated} messages for user {user.username}")
            return updated
        else:
            logger.info(f"No scheduled messages found for user {user.username}")
            return 0
            
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return 0
    except Exception as e:
        logger.error(f"Error triggering message delivery: {str(e)}")
        raise
