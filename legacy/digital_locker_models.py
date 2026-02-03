from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from cryptography.fernet import Fernet
from django.conf import settings
import uuid
import json
import base64
from datetime import timedelta

User = get_user_model()

class DigitalLocker(models.Model):
    """Main vault for a user's digital credentials"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('locked', 'Locked'),
        ('triggered', 'Death Trigger Activated'),
        ('accessed', 'Accessed by Inheritor'),
        ('expired', 'Expired'),
        ('deleted', 'Deleted'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='digital_locker')
    title = models.CharField(max_length=200, default="My Digital Legacy Vault")
    description = models.TextField(blank=True, help_text="Instructions for your inheritor")
    
    # Inheritor details
    inheritor_name = models.CharField(max_length=200)
    inheritor_email = models.EmailField()
    inheritor_phone = models.CharField(max_length=20, blank=True)
    
    # Security settings
    master_key_hash = models.TextField()  # Encrypted master key for vault
    otp_valid_hours = models.PositiveIntegerField(default=24, help_text="Hours OTP remains valid")
    access_attempts_limit = models.PositiveIntegerField(default=3)
    auto_delete_after_access = models.BooleanField(default=False)
    auto_delete_days = models.PositiveIntegerField(default=30, help_text="Days after trigger before auto-deletion")
    
    # State tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    triggered_at = models.DateTimeField(null=True, blank=True)
    accessed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'digital_locker'
        
    def __str__(self):
        return f"{self.user.username}'s Digital Locker"
    
    def generate_master_key(self):
        """Generate and store encrypted master key for this vault"""
        key = Fernet.generate_key()
        # In production, this should be encrypted with user's password or external key management
        self.master_key_hash = base64.b64encode(key).decode()
        return key
    
    def get_master_key(self):
        """Retrieve master key for encryption/decryption"""
        return base64.b64decode(self.master_key_hash.encode())
    
    def trigger_inheritance(self):
        """Trigger the inheritance process"""
        self.status = 'triggered'
        self.triggered_at = now()
        self.expires_at = now() + timedelta(days=self.auto_delete_days)
        self.save()
        
        # Generate and send OTP to inheritor
        access_token = LockerAccessToken.objects.create(
            locker=self,
            expires_at=now() + timedelta(hours=self.otp_valid_hours)
        )
        access_token.send_otp_to_inheritor()
        return access_token

class CredentialEntry(models.Model):
    """Individual credential stored in the digital locker"""
    
    CATEGORY_CHOICES = [
        ('email', 'Email Account'),
        ('banking', 'Banking & Finance'),
        ('crypto', 'Cryptocurrency'),
        ('social', 'Social Media'),
        ('cloud', 'Cloud Storage'),
        ('domain', 'Domain & Hosting'),
        ('subscription', 'Subscriptions'),
        ('other', 'Other'),
    ]
    
    locker = models.ForeignKey(DigitalLocker, on_delete=models.CASCADE, related_name='credentials')
    
    # Metadata
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    website_url = models.URLField(blank=True)
    account_identifier = models.CharField(max_length=200, blank=True, help_text="Username, email, or account ID")
    notes = models.TextField(blank=True, help_text="Additional instructions or notes")
    
    # Encrypted credential data
    encrypted_username = models.TextField(blank=True)
    encrypted_password = models.TextField(blank=True)
    encrypted_additional_data = models.TextField(blank=True, help_text="JSON of additional encrypted fields")
    
    # Priority and organization
    priority = models.PositiveIntegerField(default=1, help_text="1=Critical, 2=Important, 3=Optional")
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'credential_entry'
        ordering = ['priority', '-updated_at']
        
    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"
    
    def encrypt_field(self, value):
        """Encrypt a field value using the locker's master key"""
        if not value:
            return ""
        
        key = self.locker.get_master_key()
        f = Fernet(key)
        return f.encrypt(value.encode()).decode()
    
    def decrypt_field(self, encrypted_value):
        """Decrypt a field value using the locker's master key"""
        if not encrypted_value:
            return ""
        
        key = self.locker.get_master_key()
        f = Fernet(key)
        return f.decrypt(encrypted_value.encode()).decode()
    
    def set_username(self, username):
        """Encrypt and store username"""
        self.encrypted_username = self.encrypt_field(username)
    
    def get_username(self):
        """Decrypt and return username"""
        return self.decrypt_field(self.encrypted_username)
    
    def set_password(self, password):
        """Encrypt and store password"""
        self.encrypted_password = self.encrypt_field(password)
    
    def get_password(self):
        """Decrypt and return password"""
        return self.decrypt_field(self.encrypted_password)
    
    def set_additional_data(self, data_dict):
        """Encrypt and store additional data as JSON"""
        if data_dict:
            json_str = json.dumps(data_dict)
            self.encrypted_additional_data = self.encrypt_field(json_str)
        else:
            self.encrypted_additional_data = ""
    
    def get_additional_data(self):
        """Decrypt and return additional data as dict"""
        if self.encrypted_additional_data:
            json_str = self.decrypt_field(self.encrypted_additional_data)
            return json.loads(json_str) if json_str else {}
        return {}

class LockerAccessToken(models.Model):
    """OTP tokens for inheritor access"""
    
    locker = models.ForeignKey(DigitalLocker, on_delete=models.CASCADE, related_name='access_tokens')
    token = models.CharField(max_length=10, unique=True)
    attempts_used = models.PositiveIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    accessed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'locker_access_token'
        
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_otp()
        super().save(*args, **kwargs)
    
    def generate_otp(self):
        """Generate a secure 8-digit OTP"""
        import random
        import string
        return ''.join(random.choices(string.digits, k=8))
    
    def is_valid(self):
        """Check if token is still valid"""
        return (
            not self.is_used and 
            now() < self.expires_at and 
            self.attempts_used < self.locker.access_attempts_limit
        )
    
    def use_token(self):
        """Mark token as used and grant access"""
        if self.is_valid():
            self.is_used = True
            self.accessed_at = now()
            self.locker.status = 'accessed'
            self.locker.accessed_at = now()
            self.locker.save()
            self.save()
            return True
        return False
    
    def record_attempt(self):
        """Record a failed access attempt"""
        self.attempts_used += 1
        self.save()
        
        # Log the attempt
        LockerAccessLog.objects.create(
            locker=self.locker,
            action='failed_attempt',
            ip_address='',  # Will be set by view
            details=f"Failed OTP attempt #{self.attempts_used}"
        )
    
    def send_otp_to_inheritor(self):
        """Send OTP to inheritor via email and SMS"""
        from .email_service import DigitalLockerEmailService
        
        # Send email
        DigitalLockerEmailService.send_inheritance_notification(
            self.locker, self.token
        )
        
        # TODO: Implement SMS sending
        # self.send_sms_otp()

class LockerAccessLog(models.Model):
    """Audit log for all locker access activities"""
    
    ACTION_CHOICES = [
        ('created', 'Locker Created'),
        ('updated', 'Credentials Updated'),
        ('triggered', 'Inheritance Triggered'),
        ('otp_sent', 'OTP Sent to Inheritor'),
        ('access_granted', 'Access Granted'),
        ('failed_attempt', 'Failed Access Attempt'),
        ('viewed_credentials', 'Credentials Viewed'),
        ('exported_data', 'Data Exported'),
        ('auto_deleted', 'Auto-deleted'),
    ]
    
    locker = models.ForeignKey(DigitalLocker, on_delete=models.CASCADE, related_name='access_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'locker_access_log'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.get_action_display()} - {self.timestamp}"
