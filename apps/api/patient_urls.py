from django.urls import path

from .patient_views import PatientDetailView, PatientListCreateView

app_name = "patients"

urlpatterns = [
    path("", PatientListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", PatientDetailView.as_view(), name="detail"),
]
