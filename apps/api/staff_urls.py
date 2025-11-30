from django.urls import path

from .staff_views import StaffDetailView, StaffListCreateView

app_name = "staff_api"

urlpatterns = [
    path("", StaffListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", StaffDetailView.as_view(), name="detail"),
]
