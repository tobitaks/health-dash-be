"""
URL patterns for Medicine API.
"""

from django.urls import path

from .medicine_views import MedicineDetailView, MedicineListCreateView, MedicineOptionsView

app_name = "medicines"

urlpatterns = [
    path("", MedicineListCreateView.as_view(), name="list-create"),
    path("options/", MedicineOptionsView.as_view(), name="options"),
    path("<int:pk>/", MedicineDetailView.as_view(), name="detail"),
]
