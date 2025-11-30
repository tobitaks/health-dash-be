from django.urls import path

from .appointment_views import AppointmentDetailView, AppointmentListCreateView

app_name = "appointments"

urlpatterns = [
    path("", AppointmentListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", AppointmentDetailView.as_view(), name="detail"),
]
