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
            "middle_name",
            "last_name",
            "date_of_birth",
            "gender",
            "civil_status",
            "phone",
            "status",
            # Contact Information
            "email",
            "address_street",
            "address_city",
            "address_province",
            "address_zip",
            # Emergency Contact
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
            # Medical Information
            "blood_type",
            "allergies",
            "medical_conditions",
            "current_medications",
            # Timestamps
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "patient_id", "created_at", "updated_at")


class PatientCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating patients."""

    class Meta:
        model = Patient
        fields = (
            # Basic Info (required for create)
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "gender",
            "civil_status",
            "phone",
            "status",
            # Contact Information (optional)
            "email",
            "address_street",
            "address_city",
            "address_province",
            "address_zip",
            # Emergency Contact (optional)
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
            # Medical Information (optional)
            "blood_type",
            "allergies",
            "medical_conditions",
            "current_medications",
        )

    def validate_date_of_birth(self, value):
        if value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value
