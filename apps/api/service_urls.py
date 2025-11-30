"""
URL patterns for Service API.
"""

from django.urls import path

from .service_views import ServiceDetailView, ServiceListCreateView

app_name = "services"

urlpatterns = [
    path("", ServiceListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", ServiceDetailView.as_view(), name="detail"),
]
