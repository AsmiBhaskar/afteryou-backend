"""
Simple in-memory task queue for development when Redis is not available.
This provides a fallback mechanism for background task processing.
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from queue import Queue, Empty
from django.utils import timezone

logger = logging.getLogger(__name__)

class SimpleTaskQueue:
    """Simple in-memory task queue for development"""
    
    def __init__(self):
        self.immediate_queue = Queue()
        self.scheduled_tasks = []
        self.running = False
        self.worker_thread = None
        self.scheduler_thread = None
        self._lock = threading.Lock()
    
    def start(self):
        """Start the task queue workers"""
        if self.running:
            return
            
        self.running = True
        
        # Start immediate task worker
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        # Start scheduler worker
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Simple task queue started")
    
    def stop(self):
        """Stop the task queue workers"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Simple task queue stopped")
    
    def enqueue_immediate(self, func, *args, **kwargs):
        """Enqueue a task for immediate execution"""
        task_id = f"task_{int(time.time())}_{id(func)}"
        task = {
            'id': task_id,
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'created_at': timezone.now()
        }
        self.immediate_queue.put(task)
        logger.info(f"Enqueued immediate task {task_id}")
        return task_id
    
    def schedule_task(self, func, run_at, *args, **kwargs):
        """Schedule a task for future execution"""
        task_id = f"scheduled_{int(time.time())}_{id(func)}"
        task = {
            'id': task_id,
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'run_at': run_at,
            'created_at': timezone.now()
        }
        
        with self._lock:
            self.scheduled_tasks.append(task)
            # Keep scheduled tasks sorted by run_at
            self.scheduled_tasks.sort(key=lambda x: x['run_at'])
        
        logger.info(f"Scheduled task {task_id} for {run_at}")
        return task_id
    
    def cancel_task(self, task_id):
        """Cancel a scheduled task"""
        with self._lock:
            self.scheduled_tasks = [t for t in self.scheduled_tasks if t['id'] != task_id]
        logger.info(f"Cancelled task {task_id}")
    
    def _worker_loop(self):
        """Worker loop for immediate tasks"""
        while self.running:
            try:
                task = self.immediate_queue.get(timeout=1)
                self._execute_task(task)
                self.immediate_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in worker loop: {str(e)}")
    
    def _scheduler_loop(self):
        """Scheduler loop for delayed tasks"""
        while self.running:
            try:
                now = timezone.now()
                due_tasks = []
                
                with self._lock:
                    # Find tasks that are due
                    while self.scheduled_tasks and self.scheduled_tasks[0]['run_at'] <= now:
                        due_tasks.append(self.scheduled_tasks.pop(0))
                
                # Execute due tasks
                for task in due_tasks:
                    self._execute_task(task)
                
                # Sleep for a short interval
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
    
    def _execute_task(self, task):
        """Execute a single task"""
        try:
            logger.info(f"Executing task {task['id']}")
            result = task['func'](*task['args'], **task['kwargs'])
            logger.info(f"Task {task['id']} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Task {task['id']} failed: {str(e)}")
            raise

# Global task queue instance
_task_queue = None

def get_task_queue():
    """Get the global task queue instance"""
    global _task_queue
    if _task_queue is None:
        _task_queue = SimpleTaskQueue()
        _task_queue.start()
    return _task_queue

# Task functions that work with both Redis and simple queue
def send_single_message(message_id):
    """Send a single legacy message"""
    from .email_service import LegacyEmailService
    return LegacyEmailService.send_legacy_message(message_id)

def schedule_message_delivery(message_id, delivery_datetime):
    """Schedule a message for delivery at a specific time"""
    try:
        # Try Redis first
        import django_rq
        scheduler = django_rq.get_scheduler('email')
        job = scheduler.enqueue_at(
            delivery_datetime,
            send_single_message,
            message_id,
            job_id=f'deliver_message_{message_id}'
        )
        logger.info(f"Scheduled message {message_id} with Redis")
        return job.id
    except Exception as e:
        logger.warning(f"Redis not available, using simple queue: {str(e)}")
        # Fallback to simple queue
        queue = get_task_queue()
        job_id = queue.schedule_task(send_single_message, delivery_datetime, message_id)
        return job_id

def enqueue_immediate_delivery(message_id):
    """Queue a message for immediate delivery"""
    try:
        # Try Redis first
        import django_rq
        queue = django_rq.get_queue('email')
        job = queue.enqueue(send_single_message, message_id)
        logger.info(f"Queued message {message_id} with Redis")
        return job.id
    except Exception as e:
        logger.warning(f"Redis not available, using simple queue: {str(e)}")
        # Fallback to simple queue
        queue = get_task_queue()
        job_id = queue.enqueue_immediate(send_single_message, message_id)
        return job_id

def process_delivery_queue():
    """Process all pending deliveries"""
    from .email_service import LegacyEmailService
    return LegacyEmailService.process_pending_deliveries()
