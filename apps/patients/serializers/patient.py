from datetime import date

from rest_framework import serializers

from apps.patients.models import Patient


class PatientSerializer(serializers.ModelSerializer):
    """Serializer for reading patient data."""

    class Meta:
        model = Patient
        fields = (
            "id",
            "patient_id",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "phone",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "patient_id", "created_at", "updated_at")


class PatientCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating patients."""

    class Meta:
        model = Patient
        fields = ("first_name", "last_name", "date_of_birth", "gender", "phone", "status")

    def validate_date_of_birth(self, value):
        if value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value
