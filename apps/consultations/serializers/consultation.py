from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.consultations.models import Consultation


class ConsultationSerializer(serializers.ModelSerializer):
    """Serializer for reading consultation data."""

    patient_name = serializers.SerializerMethodField()
    appointment_ref = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Consultation
        fields = (
            "id",
            "consultation_id",
            # Relationships
            "patient",
            "patient_name",
            "appointment",
            "appointment_ref",
            "created_by",
            "created_by_name",
            # Basic Information
            "consultation_date",
            "consultation_time",
            "status",
            "chief_complaint",
            # Vital Signs
            "bp_systolic",
            "bp_diastolic",
            "temperature",
            "temperature_unit",
            "weight",
            "weight_unit",
            "height",
            "height_unit",
            "heart_rate",
            "respiratory_rate",
            "oxygen_saturation",
            # SOAP Notes
            "soap_subjective",
            "soap_objective",
            "soap_assessment",
            "soap_plan",
            # Additional Information
            "physical_exam_notes",
            "diagnosis",
            "follow_up_date",
            "follow_up_notes",
            # Timestamps
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "consultation_id", "created_at", "updated_at")

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None

    def get_appointment_ref(self, obj):
        return obj.appointment.appointment_id if obj.appointment else None

    def get_created_by_name(self, obj):
        if obj.created_by:
            name = f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
            return name or obj.created_by.email
        return None


class ConsultationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating consultations (minimal fields)."""

    class Meta:
        model = Consultation
        fields = (
            "patient",
            "appointment",
            "consultation_date",
            "consultation_time",
            "chief_complaint",
        )

    def validate_patient(self, value):
        """Ensure patient belongs to the same clinic."""
        clinic = self.context["request"].user.clinic
        if value.clinic != clinic:
            raise serializers.ValidationError(_("Patient does not belong to your clinic."))
        return value

    def validate_appointment(self, value):
        """Ensure appointment belongs to the same clinic."""
        if value is None:
            return value
        clinic = self.context["request"].user.clinic
        if value.clinic != clinic:
            raise serializers.ValidationError(_("Appointment does not belong to your clinic."))
        return value


class ConsultationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating consultations (all editable fields)."""

    class Meta:
        model = Consultation
        fields = (
            # Basic Information (editable)
            "patient",
            "appointment",
            "consultation_date",
            "consultation_time",
            "status",
            "chief_complaint",
            # Vital Signs
            "bp_systolic",
            "bp_diastolic",
            "temperature",
            "temperature_unit",
            "weight",
            "weight_unit",
            "height",
            "height_unit",
            "heart_rate",
            "respiratory_rate",
            "oxygen_saturation",
            # SOAP Notes
            "soap_subjective",
            "soap_objective",
            "soap_assessment",
            "soap_plan",
            # Additional Information
            "physical_exam_notes",
            "diagnosis",
            "follow_up_date",
            "follow_up_notes",
        )

    def validate_patient(self, value):
        """Ensure patient belongs to the same clinic."""
        clinic = self.context["request"].user.clinic
        if value.clinic != clinic:
            raise serializers.ValidationError(_("Patient does not belong to your clinic."))
        return value

    def validate_appointment(self, value):
        """Ensure appointment belongs to the same clinic."""
        if value is None:
            return value
        clinic = self.context["request"].user.clinic
        if value.clinic != clinic:
            raise serializers.ValidationError(_("Appointment does not belong to your clinic."))
        return value
