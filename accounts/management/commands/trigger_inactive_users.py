from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta
from accounts.models import User
from accounts.email_service import DeadMansSwitchEmailService
from legacy.models import LegacyMessage

class Command(BaseCommand):
    help = 'Dead mans switch: Check for inactive users and trigger notifications or message delivery.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--send-emails',
            action='store_true',
            help='Actually send notification emails (default: false for safety)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        send_emails = options['send_emails']
        
        self.stdout.write("=== Dead Man's Switch Check ===")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        if not send_emails:
            self.stdout.write(self.style.WARNING("EMAIL SENDING DISABLED - Use --send-emails to enable"))
        
        # Get all users
        all_users = User.objects.all()
        self.stdout.write(f"Checking {all_users.count()} users...")
        
        # Process each user
        for user in all_users:
            self._process_user(user, dry_run, send_emails)
    
    def _process_user(self, user, dry_run, send_emails):
        """Process individual user for dead man's switch logic"""
        current_time = now()
        
        # Calculate when user should have checked in (based on their interval)
        months_ago = 30 * user.check_in_interval_months  # Approximate months to days
        check_in_deadline = current_time - timedelta(days=months_ago)
        
        # Check if user is past their check-in deadline
        if user.last_check_in >= check_in_deadline:
            # User is active, no action needed
            return
        
        self.stdout.write(f"\n📋 Processing user: {user.username}")
        self.stdout.write(f"   Last check-in: {user.last_check_in}")
        self.stdout.write(f"   Should check in every: {user.check_in_interval_months} months")
        self.stdout.write(f"   Grace period: {user.grace_period_days} days")
        
        # Check if notification has been sent
        if user.notification_sent_at is None:
            # First stage: Send notification
            self._handle_first_notification(user, dry_run, send_emails)
        else:
            # Check if grace period has expired
            grace_deadline = user.notification_sent_at + timedelta(days=user.grace_period_days)
            
            if current_time >= grace_deadline:
                # Grace period expired: Trigger delivery
                self._handle_delivery_trigger(user, dry_run)
            else:
                # Still in grace period
                remaining_days = (grace_deadline - current_time).days
                self.stdout.write(f"   📧 Notification sent, {remaining_days} days remaining in grace period")
    
    def _handle_first_notification(self, user, dry_run, send_emails):
        """Send first inactivity notification"""
        self.stdout.write(f"   📧 Sending first inactivity notification...")
        
        if not dry_run:
            user.notification_sent_at = now()
            user.save()
            self.stdout.write(f"   ✓ Marked notification as sent")
            
            if send_emails:
                success = DeadMansSwitchEmailService.send_check_in_reminder(user)
                if success:
                    self.stdout.write(f"   ✓ Email sent successfully to {user.email}")
                else:
                    self.stdout.write(f"   ❌ Failed to send email to {user.email}")
            else:
                self.stdout.write(f"   📧 [EMAIL DISABLED] Would send reminder to {user.email}")
        else:
            self.stdout.write(f"   [DRY RUN] Would send notification to {user.email}")
    
    def _handle_delivery_trigger(self, user, dry_run):
        """Trigger message delivery for user"""
        messages = LegacyMessage.objects.filter(user=user, status='scheduled')
        message_count = messages.count()
        
        self.stdout.write(f"   🚨 Grace period expired! Triggering delivery of {message_count} messages...")
        
        if not dry_run and message_count > 0:
            # Update all scheduled messages to pending
            updated = messages.update(status='pending')
            self.stdout.write(f"   ✓ {updated} messages set to pending for delivery")
            
            # Reset user's notification status for future cycles
            user.notification_sent_at = None
            user.save()
            self.stdout.write(f"   ✓ User notification status reset")
        else:
            if message_count > 0:
                self.stdout.write(f"   [DRY RUN] Would trigger delivery of {message_count} messages")
            else:
                self.stdout.write(f"   ℹ️  No scheduled messages to deliver")
