"""
URL configuration for afteryou project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import task_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('legacy.urls')),
    path('accounts/', include('accounts.urls')),
    # API endpoints
    path('', include('legacy.api_urls')),
    path('', include('accounts.urls')),  # Also include accounts URLs at root level for dashboard/system APIs
    # JWT token endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # QStash task endpoints (serverless background tasks)
    path('api/tasks/send_check_in_reminders/', task_views.send_check_in_reminders_task, name='qstash_check_in_reminders'),
    path('api/tasks/process_scheduled_messages/', task_views.process_scheduled_messages_task, name='qstash_scheduled_messages'),
    path('api/tasks/send_final_warnings/', task_views.send_final_warnings_task, name='qstash_final_warnings'),
    path('api/tasks/process_inactive_users/', task_views.process_inactive_users_task, name='qstash_inactive_users'),
    path('api/tasks/test/', task_views.test_task, name='qstash_test'),
]
