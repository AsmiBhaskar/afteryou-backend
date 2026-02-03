
# DEPRECATED: All views in this file are deprecated in favor of DRF API endpoints in api_views.py
# Remove these after frontend migration is complete.

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from .models import LegacyMessage

def deprecated_view(*args, **kwargs):
    raise NotImplementedError("This view is deprecated. Use the DRF API endpoints instead.")

dashboard = deprecated_view

create_message = deprecated_view

message_detail = deprecated_view

schedule_message_view = deprecated_view

send_message_now = deprecated_view

delete_message = deprecated_view

test_email = deprecated_view

create_legacy = deprecated_view

# NEW CHAIN VIEWS

def chain_message_view(request, token):
    """Serve the chain message viewing page"""
    return render(request, 'legacy/chain_message_view.html', {
        'token': token
    })
