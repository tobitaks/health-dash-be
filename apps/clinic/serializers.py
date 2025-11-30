from rest_framework import serializers
from .models import Clinic


class ClinicSerializer(serializers.ModelSerializer):
    """Serializer for Clinic model."""

    owner = serializers.SerializerMethodField()
    staff_count = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()

    class Meta:
        model = Clinic
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "website",
            "address_street",
            "address_city",
            "address_region",
            "address_postal_code",
            "address_country",
            "full_address",
            "business_hours",
            "logo",
            "timezone",
            "currency",
            "is_active",
            "owner",
            "staff_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "owner", "staff_count"]

    def get_owner(self, obj):
        """Get clinic owner info."""
        owner = obj.owner
        if owner:
            return {
                "id": owner.id,
                "email": owner.email,
                "first_name": owner.first_name,
                "last_name": owner.last_name,
            }
        return None


class ClinicCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a clinic (minimal fields)."""

    class Meta:
        model = Clinic
        fields = ["name"]
