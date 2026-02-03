"""
Management command to start RQ workers for processing background tasks
"""
import logging
import sys
from django.core.management.base import BaseCommand
import django_rq
from rq import Worker

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Start RQ workers for processing legacy message tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--queue',
            type=str,
            default='default',
            choices=['default', 'email', 'all'],
            help='Queue to process (default: default, options: default, email, all)'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=1,
            help='Number of worker processes to start (default: 1)'
        )

    def handle(self, *args, **options):
        queue_name = options['queue']
        num_workers = options['workers']
        
        if queue_name == 'all':
            queues = ['default', 'email']
        else:
            queues = [queue_name]
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting {num_workers} RQ worker(s) for queue(s): {", ".join(queues)}'
            )
        )
        
        try:
            if num_workers == 1:
                # Single worker - use SimpleWorker for Windows compatibility
                if len(queues) == 1:
                    queue = django_rq.get_queue(queues[0])
                    connection = queue.connection
                else:
                    # Multiple queues, single worker
                    queue_objects = [django_rq.get_queue(q) for q in queues]
                    connection = queue_objects[0].connection
                    queue = queue_objects  # Pass list for multiple queues
                
                # Use SimpleWorker for Windows compatibility
                if sys.platform.startswith('win'):
                    from rq import SimpleWorker
                    worker = SimpleWorker(queue if isinstance(queue, list) else [queue], connection=connection)
                    self.stdout.write(f'Starting SimpleWorker (Windows mode) for queues: {queues}')
                else:
                    worker = Worker(queue if isinstance(queue, list) else [queue], connection=connection)
                    self.stdout.write(f'Starting Worker for queues: {queues}')
                
                worker.work()
            else:
                # Multiple workers - this would require multiprocessing
                self.stdout.write(
                    self.style.WARNING(
                        'Multiple workers not implemented in this command. '
                        'Run multiple instances of this command instead.'
                    )
                )
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nReceived interrupt signal, shutting down worker...')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running worker: {str(e)}')
            )
