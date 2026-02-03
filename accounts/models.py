from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now

class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    ROLE_CHOICES = (
        ('user', 'User'),
        ('executor', 'Executor'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    last_check_in = models.DateTimeField(default=now, help_text="Last time the user checked in.")
    
    # Dead man's switch settings
    check_in_interval_months = models.PositiveIntegerField(
        default=6, 
        help_text="Number of months after which user should check in"
    )
    notification_sent_at = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="When the inactivity notification was sent"
    )
    grace_period_days = models.PositiveIntegerField(
        default=10,
        help_text="Days after notification before triggering delivery"
    )
    
    def __str__(self):
        return self.username

