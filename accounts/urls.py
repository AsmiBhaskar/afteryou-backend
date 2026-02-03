from django.urls import path
from .views import register_view, login_view, logout_view, check_in_view, check_in_status_view, update_user_settings_view
from .api_views import register_api, login_api, logout_api, user_profile_api, dashboard_stats_api, system_status_api, job_status_api
from . import api_views

urlpatterns = [
    # Template-based views
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # API endpoints for React frontend
    path('api/register/', register_api, name='register_api'),
    path('api/login/', login_api, name='login_api'),
    path('api/logout/', logout_api, name='logout_api'),
    path('api/profile/', user_profile_api, name='user_profile_api'),
    
    # Dead man's switch API endpoints
    # Canonical API endpoints (mounted at root by afteryou/urls.py)
    # path('api/check-in/', ...) and path('api/settings/', ...) are included at root only
    
    # Dashboard and system monitoring API endpoints
    path('dashboard/stats/', dashboard_stats_api, name='dashboard_stats'),
    path('system/status/', system_status_api, name='system_status'),
    path('jobs/<str:job_id>/status/', job_status_api, name='job_status'),
]
