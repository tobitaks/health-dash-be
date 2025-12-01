from apps.consultations.serializers.consultation import (
    ConsultationBasicUpdateSerializer,
    ConsultationCreateSerializer,
    ConsultationDiagnosisUpdateSerializer,
    ConsultationFollowUpUpdateSerializer,
    ConsultationPhysicalExamUpdateSerializer,
    ConsultationSerializer,
    ConsultationSOAPUpdateSerializer,
    ConsultationVitalsUpdateSerializer,
)

__all__ = [
    "ConsultationSerializer",
    "ConsultationCreateSerializer",
    # Section-specific update serializers
    "ConsultationBasicUpdateSerializer",
    "ConsultationVitalsUpdateSerializer",
    "ConsultationSOAPUpdateSerializer",
    "ConsultationDiagnosisUpdateSerializer",
    "ConsultationPhysicalExamUpdateSerializer",
    "ConsultationFollowUpUpdateSerializer",
]
