from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import api_views
from accounts.api_views import api_check_in, api_check_in_status

urlpatterns = [
    # Authentication endpoints
    path('api/auth/login/', api_views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/register/', api_views.register_user, name='api_register'),
    path('api/auth/profile/', api_views.user_profile, name='api_user_profile'),
    path('api/settings/', api_views.user_settings, name='api_user_settings'),
    path('accounts/api/settings/', api_views.user_settings, name='api_user_settings_accounts'),
    path('api/check-in/', api_check_in, name='api_check_in'),
    path('api/check-in/status/', api_check_in_status, name='api_check_in_status'),
    
    # Messages endpoints
    path('api/messages/', api_views.LegacyMessageListCreateView.as_view(), name='api_messages_list'),
    path('api/messages/<str:id>/', api_views.LegacyMessageDetailView.as_view(), name='api_message_detail'),
    
    # Dashboard & Actions
    path('api/dashboard/stats/', api_views.dashboard_stats, name='api_dashboard_stats'),
    path('api/system/status/', api_views.system_status, name='api_system_status'),
    path('api/jobs/<str:job_id>/status/', api_views.job_status, name='api_job_status'),
    path('api/messages/send-test/', api_views.send_test_message, name='api_send_test'),
    path('api/messages/schedule/', api_views.schedule_message_api, name='api_schedule_message'),
    
    # Chain functionality endpoints
    path('api/legacy/chain/<uuid:token>/', api_views.view_message_by_token, name='view_message_by_token'),
    path('api/legacy/chain/<uuid:token>/extend/', api_views.extend_chain, name='extend_chain'),
    path('api/legacy/chain/<uuid:token>/full/', api_views.view_full_chain, name='view_full_chain'),
    path('api/legacy/chains/', api_views.user_chains, name='user_chains'),
]
