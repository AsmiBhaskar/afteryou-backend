"""
Management command to start the message delivery scheduler
This command runs the periodic task that checks for messages due for delivery
"""
import time
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import django_rq
from legacy.tasks import process_delivery_queue

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Start the legacy message delivery scheduler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=300,  # 5 minutes
            help='Check interval in seconds (default: 300)'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run as a daemon process'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        is_daemon = options['daemon']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting message delivery scheduler (checking every {interval} seconds)'
            )
        )
        
        if is_daemon:
            self.run_daemon(interval)
        else:
            self.run_once()

    def run_once(self):
        """Run the delivery queue processing once"""
        try:
            self.stdout.write('Processing delivery queue...')
            
            # Get the queue and enqueue the processing task
            queue = django_rq.get_queue('email')
            job = queue.enqueue(process_delivery_queue)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Delivery queue processing job enqueued with ID: {job.id}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error starting delivery queue processing: {str(e)}')
            )

    def run_daemon(self, interval):
        """Run as a daemon, continuously scheduling delivery checks"""
        try:
            while True:
                self.stdout.write(f'[{timezone.now()}] Scheduling delivery queue check...')
                
                # Get the queue and enqueue the processing task
                queue = django_rq.get_queue('email')
                job = queue.enqueue(process_delivery_queue)
                
                self.stdout.write(f'Job {job.id} enqueued for delivery processing')
                
                # Wait for the specified interval
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nReceived interrupt signal, shutting down scheduler...')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error in scheduler daemon: {str(e)}')
            )
