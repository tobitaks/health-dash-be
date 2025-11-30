"""
URL patterns for policy API.
"""

from django.urls import path

from .role_views import PolicyListView

app_name = "policies"

urlpatterns = [
    path("", PolicyListView.as_view(), name="list"),
]
