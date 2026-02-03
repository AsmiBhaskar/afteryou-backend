"""
Management command to set up QStash recurring schedules.
Run this once after deployment to configure all background tasks.

Usage:
    python manage.py setup_qstash_schedules
    python manage.py setup_qstash_schedules --clear  # Clear existing schedules first
"""
from django.core.management.base import BaseCommand
from afteryou.qstash_service import qstash


class Command(BaseCommand):
    help = 'Set up QStash recurring schedules for background tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing schedules before creating new ones',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up QStash schedules...'))
        
        # Clear existing schedules if requested
        if options['clear']:
            self.stdout.write('Clearing existing schedules...')
            try:
                schedules = qstash.list_schedules()
                for schedule in schedules:
                    # Handle both dict and object responses
                    if hasattr(schedule, 'schedule_id'):
                        schedule_id = schedule.schedule_id
                    elif hasattr(schedule, 'scheduleId'):
                        schedule_id = schedule.scheduleId
                    elif isinstance(schedule, dict):
                        schedule_id = schedule.get('scheduleId') or schedule.get('schedule_id')
                    else:
                        schedule_id = str(schedule)
                    
                    if schedule_id:
                        qstash.delete_schedule(schedule_id)
                        self.stdout.write(f'  Deleted schedule: {schedule_id}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error clearing schedules: {str(e)}'))
        
        # Define schedules
        schedules_to_create = [
            {
                'task_name': 'send_check_in_reminders',
                'cron': '0 9 * * *',  # Daily at 9 AM UTC (2:30 PM IST)
                'description': 'Send daily check-in reminder emails'
            },
            {
                'task_name': 'process_scheduled_messages',
                'cron': '*/15 * * * *',  # Every 15 minutes
                'description': 'Process and send scheduled legacy messages'
            },
            {
                'task_name': 'send_final_warnings',
                'cron': '0 10 * * *',  # Daily at 10 AM UTC (3:30 PM IST)
                'description': 'Send final warning emails to inactive users'
            },
            {
                'task_name': 'process_inactive_users',
                'cron': '0 2 * * *',  # Daily at 2 AM UTC (7:30 AM IST)
                'description': 'Process users who exceeded grace period'
            }
        ]
        
        # Create schedules
        created_count = 0
        for schedule_config in schedules_to_create:
            try:
                schedule_id = qstash.schedule_recurring_task(
                    task_name=schedule_config['task_name'],
                    cron_expression=schedule_config['cron']
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Created schedule: {schedule_config['description']}\n"
                        f"  Task: {schedule_config['task_name']}\n"
                        f"  Cron: {schedule_config['cron']}\n"
                        f"  Schedule ID: {schedule_id}\n"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Failed to create schedule for {schedule_config['task_name']}: {str(e)}"
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully created {created_count}/{len(schedules_to_create)} schedules')
        )
        self.stdout.write(
            self.style.WARNING(
                '\nNote: Make sure your BACKEND_URL environment variable is set correctly '
                'and your server is publicly accessible for QStash to send requests.'
            )
        )
