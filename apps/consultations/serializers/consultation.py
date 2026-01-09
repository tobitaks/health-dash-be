from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.consultations.models import Consultation
from apps.utils.sanitization import sanitize_text


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
            # Structured Diagnosis
            "primary_diagnosis",
            "secondary_diagnoses",
            "differential_diagnoses",
            # Physical Examination
            "physical_exam",
            # Additional Information
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

    # Date and time are optional - will default to now if not provided
    consultation_date = serializers.DateField(required=False)
    consultation_time = serializers.TimeField(required=False)
    # Chief complaint is optional - can be added later in detail view
    chief_complaint = serializers.CharField(required=False, allow_blank=True)

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

    def validate_chief_complaint(self, value):
        """Sanitize chief complaint to prevent XSS."""
        return sanitize_text(value)


# =============================================================================
# Section-Specific Update Serializers
# =============================================================================


class ConsultationBasicUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating basic consultation info."""

    class Meta:
        model = Consultation
        fields = ("chief_complaint", "consultation_date", "consultation_time", "status")

    def validate_chief_complaint(self, value):
        """Sanitize chief complaint to prevent XSS."""
        return sanitize_text(value)


class ConsultationVitalsUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating vital signs."""

    class Meta:
        model = Consultation
        fields = (
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
        )


class ConsultationSOAPUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating SOAP notes."""

    class Meta:
        model = Consultation
        fields = ("soap_subjective", "soap_objective", "soap_assessment", "soap_plan")

    def validate_soap_subjective(self, value):
        """Sanitize SOAP subjective notes to prevent XSS."""
        return sanitize_text(value)

    def validate_soap_objective(self, value):
        """Sanitize SOAP objective notes to prevent XSS."""
        return sanitize_text(value)

    def validate_soap_assessment(self, value):
        """Sanitize SOAP assessment notes to prevent XSS."""
        return sanitize_text(value)

    def validate_soap_plan(self, value):
        """Sanitize SOAP plan notes to prevent XSS."""
        return sanitize_text(value)


class ConsultationDiagnosisUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating diagnosis fields."""

    class Meta:
        model = Consultation
        fields = ("primary_diagnosis", "secondary_diagnoses", "differential_diagnoses")

    def validate_secondary_diagnoses(self, value):
        """Ensure secondary_diagnoses is a list of strings."""
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError(_("Secondary diagnoses must be a list."))
        return value

    def validate_differential_diagnoses(self, value):
        """Ensure differential_diagnoses is a list of strings."""
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError(_("Differential diagnoses must be a list."))
        return value


class ConsultationPhysicalExamUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating physical examination."""

    class Meta:
        model = Consultation
        fields = ("physical_exam",)

    def validate_physical_exam(self, value):
        """Ensure physical_exam is a dict."""
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError(_("Physical exam must be an object."))
        return value


class ConsultationFollowUpUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating follow-up information."""

    class Meta:
        model = Consultation
        fields = ("follow_up_date", "follow_up_notes")

    def validate_follow_up_notes(self, value):
        """Sanitize follow-up notes to prevent XSS."""
        return sanitize_text(value)
