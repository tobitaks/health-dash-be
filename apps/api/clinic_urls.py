from django.urls import path

from .clinic_views import CurrentClinicView

urlpatterns = [
    path("", CurrentClinicView.as_view(), name="current_clinic"),
]
