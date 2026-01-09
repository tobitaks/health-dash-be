"""
URL patterns for Prescription API.
"""

from django.urls import path

from .prescription_views import (
    ConsultationPrescriptionView,
    PrescriptionDetailView,
    PrescriptionListCreateView,
)

app_name = "prescriptions"

urlpatterns = [
    path("", PrescriptionListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", PrescriptionDetailView.as_view(), name="detail"),
    path(
        "consultation/<int:consultation_id>/",
        ConsultationPrescriptionView.as_view(),
        name="consultation-prescription",
    ),
]
