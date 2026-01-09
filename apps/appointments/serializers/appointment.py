from datetime import date

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.appointments.models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for reading appointment data."""

    patient_name = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = (
            "id",
            "appointment_id",
            "patient",
            "patient_name",
            "service",
            "service_name",
            "assigned_to",
            "assigned_to_name",
            "date",
            "time",
            "duration_minutes",
            "status",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "appointment_id", "created_at", "updated_at")

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None

    def get_service_name(self, obj):
        return obj.service.name if obj.service else None

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip() or obj.assigned_to.email
        return None


class AppointmentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating appointments."""

    class Meta:
        model = Appointment
        fields = ("patient", "service", "assigned_to", "date", "time", "duration_minutes", "status", "notes")

    def validate_patient(self, value):
        """Ensure patient belongs to the same clinic."""
        clinic = self.context["request"].user.clinic
        if value.clinic != clinic:
            raise serializers.ValidationError(_("Patient does not belong to your clinic."))
        return value

    def validate_service(self, value):
        """Ensure service belongs to the same clinic."""
        if value is None:
            return value
        clinic = self.context["request"].user.clinic
        if value.clinic != clinic:
            raise serializers.ValidationError(_("Service does not belong to your clinic."))
        return value

    def validate_date(self, value):
        """Ensure appointment date is not in the past for new appointments."""
        if not self.instance and value < date.today():
            raise serializers.ValidationError(_("Appointment date cannot be in the past."))
        return value
