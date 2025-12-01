from django.urls import path

from apps.api.consultation_views import (
    ConsultationDetailView,
    ConsultationListCreateView,
    GenerateSOAPView,
)

urlpatterns = [
    path("", ConsultationListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", ConsultationDetailView.as_view(), name="detail"),
    path("<int:pk>/generate-soap/", GenerateSOAPView.as_view(), name="generate-soap"),
]
