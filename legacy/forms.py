from django import forms
from datetime import datetime, timedelta
from .models import LegacyMessage

class LegacyMessageForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter message title...'
        })
    )
    
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Write your legacy message here...'
        })
    )
    
    recipient_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'recipient@example.com'
        })
    )
    
    delivery_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        help_text="When should this message be delivered?"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set minimum date to tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        self.fields['delivery_date'].widget.attrs['min'] = tomorrow
    
    def clean_delivery_date(self):
        delivery_date = self.cleaned_data['delivery_date']
        if delivery_date <= datetime.now():
            raise forms.ValidationError("Delivery date must be in the future.")
        return delivery_date
    
    def save(self, user):
        """Save the form data as a LegacyMessage"""
        message = LegacyMessage(
            user_id=str(user.id),
            title=self.cleaned_data['title'],
            content=self.cleaned_data['content'],
            recipient_email=self.cleaned_data['recipient_email'],
            delivery_date=self.cleaned_data['delivery_date'],
            status='created'
        )
        message.save()
        return message
