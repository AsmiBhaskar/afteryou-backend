"""
Management command to monitor Redis queues and job status
"""
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
import django_rq
from rq.job import Job

class Command(BaseCommand):
    help = 'Monitor Redis queues and job status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--refresh',
            type=int,
            default=5,
            help='Refresh interval in seconds (default: 5)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run once instead of continuous monitoring'
        )

    def handle(self, *args, **options):
        refresh_interval = options['refresh']
        run_once = options['once']
        
        self.stdout.write(
            self.style.SUCCESS('Redis Queue Monitor Starting...')
        )
        
        try:
            if run_once:
                self.display_status()
            else:
                self.monitor_continuous(refresh_interval)
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nMonitoring stopped by user')
            )

    def display_status(self):
        """Display current queue status"""
        self.stdout.write(f'\n[{timezone.now().strftime("%Y-%m-%d %H:%M:%S")}] Queue Status:')
        self.stdout.write('=' * 60)
        
        # Check each queue
        for queue_name in ['default', 'email']:
            try:
                queue = django_rq.get_queue(queue_name)
                
                # Get queue statistics
                pending_jobs = len(queue)
                started_jobs = queue.started_job_registry.count
                finished_jobs = queue.finished_job_registry.count
                failed_jobs = queue.failed_job_registry.count
                deferred_jobs = queue.deferred_job_registry.count
                
                self.stdout.write(f'\n{queue_name.upper()} Queue:')
                self.stdout.write(f'  Pending: {pending_jobs}')
                self.stdout.write(f'  Started: {started_jobs}')
                self.stdout.write(f'  Finished: {finished_jobs}')
                self.stdout.write(f'  Failed: {failed_jobs}')
                self.stdout.write(f'  Deferred: {deferred_jobs}')
                
                # Show recent jobs
                if pending_jobs > 0:
                    self.stdout.write(f'  Recent pending jobs:')
                    for job in queue.get_jobs()[:3]:
                        self.stdout.write(f'    - {job.id}: {job.func_name}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error checking {queue_name} queue: {str(e)}')
                )
        
        # Check scheduler
        try:
            scheduler = django_rq.get_scheduler('email')
            scheduled_jobs = list(scheduler.get_jobs())
            self.stdout.write(f'\nSCHEDULER:')
            self.stdout.write(f'  Scheduled jobs: {len(scheduled_jobs)}')
            
            if scheduled_jobs:
                self.stdout.write(f'  Upcoming jobs:')
                for job in scheduled_jobs[:3]:
                    self.stdout.write(f'    - {job.id}: {job.func_name} at {job.scheduled_for}')
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error checking scheduler: {str(e)}')
            )

    def monitor_continuous(self, refresh_interval):
        """Monitor queues continuously"""
        self.stdout.write(f'Monitoring every {refresh_interval} seconds (Ctrl+C to stop)...\n')
        
        while True:
            # Clear screen
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
            
            self.display_status()
            time.sleep(refresh_interval)
