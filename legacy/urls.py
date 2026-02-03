from django.urls import path
from .views import (
    dashboard, create_message, message_detail, delete_message, 
    schedule_message_view, send_message_now, test_email, create_legacy,
    chain_message_view
)
from .digital_locker_views import (
    DigitalLockerView, CredentialView, InheritanceAccessView, trigger_inheritance
)

app_name = 'legacy'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('create/', create_message, name='create_message'),
    path('message/<str:message_id>/', message_detail, name='message_detail'),
    path('message/<str:message_id>/delete/', delete_message, name='delete_message'),
    path('message/<str:message_id>/schedule/', schedule_message_view, name='schedule_message'),
    path('message/<str:message_id>/send-now/', send_message_now, name='send_message_now'),
    path('test-email/', test_email, name='test_email'),
    path('test-legacy/', create_legacy, name='test_legacy'),  # Keep for testing
    
    # Chain functionality URLs
    path('legacy/message/<uuid:token>/', chain_message_view, name='chain_message_view'),
    
    # Digital Locker URLs
    path('api/digital-locker/', DigitalLockerView.as_view(), name='digital_locker'),
    path('api/digital-locker/credentials/', CredentialView.as_view(), name='credentials_list'),
    path('api/digital-locker/credentials/<int:credential_id>/', CredentialView.as_view(), name='credential_detail'),
    path('api/digital-locker/trigger-inheritance/', trigger_inheritance, name='trigger_inheritance'),
    path('api/digital-locker/<int:locker_id>/access/', InheritanceAccessView.as_view(), name='inheritance_access'),
]
