"""
Email service for legacy message delivery
Handles email composition, sending, and delivery tracking
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from .models import LegacyMessage

logger = logging.getLogger(__name__)

class LegacyEmailService:
    """
    Service class for handling legacy message email delivery
    """
    
    @staticmethod
    def send_legacy_message(message_id, template_name=None):
        """
        Send a single legacy message via email
        
        Args:
            message_id (str): MongoDB ObjectId of the message to send
            template_name (str): Optional custom template name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the message from database
            message = LegacyMessage.objects.get(id=message_id)
            
            # Determine email subject based on message type
            if message.parent_message:
                subject = f"Legacy Chain Message: {message.title}"
            else:
                subject = f"Legacy Message: {message.title}"
            
            # Create HTML email content with appropriate template
            if template_name:
                html_content = LegacyEmailService._render_email_template(message, template_name)
            else:
                # Choose template based on message type
                if message.parent_message:
                    html_content = LegacyEmailService._render_chain_email_template(message)
                else:
                    html_content = LegacyEmailService._render_email_template(message)
            
            # Create plain text fallback
            if message.parent_message:
                text_content = f"""
{message.title}

{message.content}

---
This is part of a legacy chain (Generation {message.generation}).
Added by: {message.sender_name or 'Anonymous'}

View the full chain and add your own message:
{settings.FRONTEND_URL}/legacy/message/{message.recipient_access_token}

Sent via AfterYou Legacy Messages.
                """.strip()
            else:
                text_content = f"""
{message.title}

{message.content}

---
This message was scheduled to be delivered on {message.delivery_date.strftime('%B %d, %Y at %I:%M %p')}.
View and extend this legacy:
{settings.FRONTEND_URL}/legacy/message/{message.recipient_access_token}

Sent via AfterYou Legacy Messages.
                """.strip()
            
            # Send email using Django's email system
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[message.recipient_email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send the email
            sent = email.send()
            
            if sent:
                # Update message status
                message.status = 'sent'
                message.sent_at = timezone.now()
                message.save()
                
                logger.info(f"Successfully sent legacy message {message_id} to {message.recipient_email}")
                return True
            else:
                # Mark as failed
                message.status = 'failed'
                message.save()
                
                logger.error(f"Failed to send legacy message {message_id}")
                return False
                
        except LegacyMessage.DoesNotExist:
            logger.error(f"Message {message_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error sending message {message_id}: {str(e)}")
            
            # Try to update message status to failed
            try:
                message = LegacyMessage.objects.get(id=message_id)
                message.status = 'failed'
                message.save()
            except:
                pass
                
            return False
    
    @staticmethod
    def _render_email_template(message):
        """
        Render HTML email template for legacy message
        
        Args:
            message (LegacyMessage): The message object
            
        Returns:
            str: Rendered HTML content
        """
        try:
            # Try to use a template if it exists
            return render_to_string('legacy/email_template.html', {
                'message': message,
                'delivery_date': message.delivery_date,
                'sent_date': timezone.now(),
            })
        except:
            # Fallback to simple HTML if template doesn't exist
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Legacy Message: {message.title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #6B73FF;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .title {{
            color: #6B73FF;
            font-size: 28px;
            margin: 0;
            font-weight: 600;
        }}
        .subtitle {{
            color: #666;
            margin: 10px 0 0 0;
            font-size: 14px;
        }}
        .content {{
            font-size: 16px;
            line-height: 1.8;
            margin-bottom: 30px;
            white-space: pre-wrap;
        }}
        .footer {{
            border-top: 1px solid #eee;
            padding-top: 20px;
            font-size: 12px;
            color: #999;
            text-align: center;
        }}
        .date-info {{
            background: #f0f2ff;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #6B73FF;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">{message.title}</h1>
            <p class="subtitle">A Legacy Message from AfterYou</p>
        </div>
        
        <div class="content">
{message.content}
        </div>
        
        <div class="date-info">
            <strong>Scheduled for delivery:</strong> {message.delivery_date.strftime('%B %d, %Y at %I:%M %p')}<br>
            <strong>Delivered on:</strong> {timezone.now().strftime('%B %d, %Y at %I:%M %p')}
        </div>
        
        <div class="footer">
            <p>This message was created and scheduled through AfterYou Legacy Messages.<br>
            A service for connecting present moments with future hearts.</p>
            <p><a href="{settings.FRONTEND_URL}/legacy/message/{message.recipient_access_token}" style="color: #6B73FF;">View & Extend This Legacy</a></p>
        </div>
    </div>
</body>
</html>
            """
    
    @staticmethod
    def _render_chain_email_template(message):
        """
        Render HTML email template for chain legacy message
        
        Args:
            message (LegacyMessage): The chain message object
            
        Returns:
            str: Rendered HTML content
        """
        try:
            # Try to use a template if it exists
            return render_to_string('legacy/chain_email_template.html', {
                'message': message,
                'parent_message': message.parent_message,
                'delivery_date': message.delivery_date,
                'sent_date': timezone.now(),
                'frontend_url': settings.FRONTEND_URL,
            })
        except:
            # Fallback to simple HTML if template doesn't exist
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Legacy Chain Message: {message.title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #9C27B0;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .title {{
            color: #9C27B0;
            font-size: 28px;
            margin: 0;
            font-weight: 600;
        }}
        .subtitle {{
            color: #666;
            margin: 10px 0 0 0;
            font-size: 14px;
        }}
        .chain-info {{
            background: #f3e5f5;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #9C27B0;
        }}
        .content {{
            font-size: 16px;
            line-height: 1.8;
            margin-bottom: 30px;
            white-space: pre-wrap;
        }}
        .footer {{
            border-top: 1px solid #eee;
            padding-top: 20px;
            font-size: 12px;
            color: #999;
            text-align: center;
        }}
        .action-buttons {{
            text-align: center;
            margin: 30px 0;
        }}
        .btn {{
            display: inline-block;
            padding: 12px 24px;
            margin: 10px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
        }}
        .btn-primary {{
            background-color: #9C27B0;
            color: white;
        }}
        .btn-secondary {{
            background-color: #6B73FF;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">{message.title}</h1>
            <p class="subtitle">A Legacy Chain Message from AfterYou</p>
        </div>
        
        <div class="chain-info">
            <strong>🔗 This is Generation {message.generation} of a Legacy Chain</strong><br>
            <small>Added by: {message.sender_name or 'Anonymous'}</small>
        </div>
        
        <div class="content">
{message.content}
        </div>
        
        <div class="action-buttons">
            <a href="{settings.FRONTEND_URL}/legacy/message/{message.recipient_access_token}" class="btn btn-primary">View Message</a>
            <a href="{settings.FRONTEND_URL}/legacy/message/{message.recipient_access_token}/extend" class="btn btn-secondary">Add Your Message & Pass It Forward</a>
        </div>
        
        <div class="footer">
            <p>This legacy chain continues the memories across generations.<br>
            <a href="{settings.FRONTEND_URL}/legacy/message/{message.recipient_access_token}/chain" style="color: #9C27B0;">View Full Chain History</a></p>
            <p>Sent via AfterYou Legacy Messages.</p>
        </div>
    </div>
</body>
</html>
            """
    
    @staticmethod
    def process_pending_deliveries():
        """
        Process all messages that are due for delivery
        
        Returns:
            dict: Results summary with counts
        """
        logger.info("Processing pending message deliveries...")
        
        try:
            # Get all scheduled messages that are due for delivery
            current_time = timezone.now()
            due_messages = LegacyMessage.objects.filter(
                status='scheduled',
                delivery_date__lte=current_time
            )
            
            total_processed = 0
            successful = 0
            failed = 0
            
            for message in due_messages:
                total_processed += 1
                
                if LegacyEmailService.send_legacy_message(str(message.id)):
                    successful += 1
                else:
                    failed += 1
            
            results = {
                'total_processed': total_processed,
                'successful': successful,
                'failed': failed,
                'timestamp': current_time
            }
            
            logger.info(f"Delivery batch completed: {successful} successful, {failed} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error processing pending deliveries: {str(e)}")
            return {
                'error': str(e),
                'total_processed': 0,
                'successful': 0,
                'failed': 0
            }
    
    @staticmethod
    def schedule_message_for_delivery(message_id):
        """
        Mark a message as scheduled for delivery
        
        Args:
            message_id (str): MongoDB ObjectId of the message
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            message = LegacyMessage.objects.get(id=message_id)
            
            # Check if delivery date is in the future
            if message.delivery_date > timezone.now():
                message.status = 'scheduled'
                message.save()
                
                logger.info(f"Message {message_id} scheduled for delivery at {message.delivery_date}")
                return True
            else:
                # If delivery date has passed, send immediately
                logger.info(f"Message {message_id} delivery date has passed, sending immediately")
                return LegacyEmailService.send_legacy_message(message_id)
                
        except LegacyMessage.DoesNotExist:
            logger.error(f"Message {message_id} not found for scheduling")
            return False
        except Exception as e:
            logger.error(f"Error scheduling message {message_id}: {str(e)}")
            return False
    
    @staticmethod
    def send_test_message(message_id):
        """
        Send a test version of the message immediately
        
        Args:
            message_id (str): MongoDB ObjectId of the message
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            message = LegacyMessage.objects.get(id=message_id)
            
            # Create a copy for testing but mark it clearly as a test
            subject = f"[TEST] Legacy Message: {message.title}"
            
            html_content = LegacyEmailService._render_email_template(message)
            # Add test notice to HTML content
            html_content = html_content.replace(
                '<div class="container">',
                '<div class="container"><div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin-bottom: 20px; border-radius: 4px; color: #856404;"><strong>🧪 TEST MESSAGE</strong> - This is a test delivery of your legacy message.</div>'
            )
            
            text_content = f"""
🧪 TEST MESSAGE - This is a test delivery of your legacy message.

{message.title}

{message.content}

---
This message was scheduled to be delivered on {message.delivery_date.strftime('%B %d, %Y at %I:%M %p')}.
TEST sent via AfterYou Legacy Messages.
            """.strip()
            
            # Send test email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[message.recipient_email]
            )
            email.attach_alternative(html_content, "text/html")
            
            sent = email.send()
            
            if sent:
                logger.info(f"Successfully sent test message {message_id} to {message.recipient_email}")
                return True
            else:
                logger.error(f"Failed to send test message {message_id}")
                return False
                
        except LegacyMessage.DoesNotExist:
            logger.error(f"Message {message_id} not found for test sending")
            return False
        except Exception as e:
            logger.error(f"Error sending test message {message_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_delivery_stats():
        """
        Get statistics about message deliveries
        
        Returns:
            dict: Delivery statistics
        """
        try:
            total_messages = LegacyMessage.objects.count()
            scheduled_messages = LegacyMessage.objects.filter(status='scheduled').count()
            sent_messages = LegacyMessage.objects.filter(status='sent').count()
            failed_messages = LegacyMessage.objects.filter(status='failed').count()
            created_messages = LegacyMessage.objects.filter(status='created').count()
            
            return {
                'total': total_messages,
                'scheduled': scheduled_messages,
                'sent': sent_messages,
                'failed': failed_messages,
                'created': created_messages,
                'delivery_rate': (sent_messages / total_messages * 100) if total_messages > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting delivery stats: {str(e)}")
            return {
                'error': str(e),
                'total': 0,
                'scheduled': 0,
                'sent': 0,
                'failed': 0,
                'created': 0,
                'delivery_rate': 0
            }
