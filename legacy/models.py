from mongoengine import Document, StringField, DateTimeField, EmailField, ReferenceField, IntField, UUIDField
from datetime import datetime
from accounts.models import User
import uuid

# Import the digital locker models
from .digital_locker_models import DigitalLocker, CredentialEntry, LockerAccessToken, LockerAccessLog

class LegacyMessage(Document):
    user_id = StringField(required=True)  
    title = StringField(required=True, max_length=200)
    content = StringField()
    recipient_email = EmailField(required=True)
    delivery_date = DateTimeField(required=True)
    
    # Chain functionality - NEW FIELDS
    parent_message = ReferenceField('self', null=True)  # Links to the original message
    chain_id = UUIDField(default=uuid.uuid4)  # Groups all messages in same chain
    generation = IntField(default=1)  # 1st gen = original, 2nd gen = first reply, etc.
    sender_name = StringField(max_length=100)  # For anonymous chain contributors
    
    # Access control for recipients
    recipient_access_token = UUIDField(default=uuid.uuid4)  # Token for recipients to access/reply
    
    # Status tracking
    STATUS_CHOICES = (
        ('created', 'Created'),
        ('scheduled', 'Scheduled'),
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    status = StringField(max_length=10, choices=STATUS_CHOICES, default='created')
    created_at = DateTimeField(default=datetime.utcnow)
    sent_at = DateTimeField()
    
    # Background job tracking
    job_id = StringField()  # RQ job ID for tracking background tasks
    
    # Meta configuration
    meta = {
        'collection': 'legacy_messages',
        'ordering': ['-created_at'],
        'indexes': ['chain_id', 'parent_message', 'recipient_access_token', 'generation']
    }
    
    def __str__(self):
        return f"{self.title} - {self.recipient_email} (Gen {self.generation})"