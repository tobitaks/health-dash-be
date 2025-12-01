from django.urls import path

from apps.api.consultation_views import (
    ConsultationDetailView,
    ConsultationListCreateView,
    GenerateSOAPView,
    UpdateBasicView,
    UpdateDiagnosisView,
    UpdateFollowUpView,
    UpdatePhysicalExamView,
    UpdateSOAPView,
    UpdateVitalsView,
)

urlpatterns = [
    path("", ConsultationListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", ConsultationDetailView.as_view(), name="detail"),
    path("<int:pk>/generate-soap/", GenerateSOAPView.as_view(), name="generate-soap"),
    # Section-specific update endpoints
    path("<int:pk>/basic/", UpdateBasicView.as_view(), name="update-basic"),
    path("<int:pk>/vitals/", UpdateVitalsView.as_view(), name="update-vitals"),
    path("<int:pk>/soap/", UpdateSOAPView.as_view(), name="update-soap"),
    path("<int:pk>/diagnosis/", UpdateDiagnosisView.as_view(), name="update-diagnosis"),
    path("<int:pk>/physical-exam/", UpdatePhysicalExamView.as_view(), name="update-physical-exam"),
    path("<int:pk>/follow-up/", UpdateFollowUpView.as_view(), name="update-follow-up"),
]
