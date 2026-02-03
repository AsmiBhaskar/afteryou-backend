"""
Upstash QStash Service for serverless background task processing.
Replaces Celery workers with serverless HTTP-based task queue.
"""
import os
import json
from datetime import datetime, timedelta
from decouple import config
from upstash_qstash import QStash

class QStashService:
    """Wrapper for QStash client with helper methods for task publishing."""
    
    def __init__(self):
        self.client = QStash(config('QSTASH_TOKEN'))
        self.backend_url = config('BACKEND_URL', default='http://localhost:8000')
    
    def publish_task(self, task_name, payload=None, delay_seconds=0):
        """
        Publish a task to QStash for immediate or delayed execution.
        
        Args:
            task_name: Name of the task (corresponds to URL endpoint)
            payload: Dictionary of data to send to the task
            delay_seconds: Optional delay before execution
        
        Returns:
            Response from QStash with message ID
        """
        url = f"{self.backend_url}/api/tasks/{task_name}/"
        
        params = {
            "url": url,
            "body": json.dumps(payload or {}),
            "headers": {"Content-Type": "application/json"}
        }
        
        if delay_seconds > 0:
            params["delay"] = f"{delay_seconds}s"
        
        try:
            response = self.client.message.publish(**params)
            print(f"✓ Task '{task_name}' published to QStash. Message ID: {response['messageId']}")
            return response
        except Exception as e:
            print(f"✗ Failed to publish task '{task_name}': {str(e)}")
            raise
    
    def schedule_recurring_task(self, task_name, cron_expression, payload=None):
        """
        Schedule a recurring task with cron expression.
        
        Args:
            task_name: Name of the task
            cron_expression: Cron expression (e.g., "0 9 * * *" for daily at 9 AM)
            payload: Dictionary of data to send to the task
        
        Returns:
            Schedule ID from QStash
        
        Example cron expressions:
            - "*/15 * * * *" - Every 15 minutes
            - "0 */4 * * *" - Every 4 hours
            - "0 9 * * *" - Daily at 9 AM UTC
            - "0 0 * * 0" - Weekly on Sunday at midnight
        """
        url = f"{self.backend_url}/api/tasks/{task_name}/"
        
        try:
            response = self.client.schedule.create(
                destination=url,
                cron=cron_expression,
                body=json.dumps(payload or {}),
                headers={"Content-Type": "application/json"}
            )
            schedule_id = response.get('scheduleId')
            print(f"✓ Recurring task '{task_name}' scheduled with cron: {cron_expression}. Schedule ID: {schedule_id}")
            return schedule_id
        except Exception as e:
            print(f"✗ Failed to schedule recurring task '{task_name}': {str(e)}")
            raise
    
    def list_schedules(self):
        """List all scheduled tasks."""
        try:
            schedules = self.client.schedule.list()
            return schedules
        except Exception as e:
            print(f"✗ Failed to list schedules: {str(e)}")
            raise
    
    def delete_schedule(self, schedule_id):
        """Delete a scheduled task by ID."""
        try:
            self.client.schedule.delete(schedule_id)
            print(f"✓ Schedule {schedule_id} deleted successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to delete schedule {schedule_id}: {str(e)}")
            raise


# Singleton instance
qstash = QStashService()
