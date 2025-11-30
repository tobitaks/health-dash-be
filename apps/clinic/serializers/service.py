from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.clinic.models import Service


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for listing services."""

    class Meta:
        model = Service
        fields = ("id", "name", "code", "price", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating services."""

    class Meta:
        model = Service
        fields = ("name", "code", "price", "is_active")

    def validate_code(self, value):
        """Ensure code is unique within the clinic."""
        clinic = self.context["request"].user.clinic
        instance = self.instance

        queryset = Service.objects.filter(clinic=clinic, code__iexact=value)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(_("A service with this code already exists in your clinic."))

        return value.upper()  # Normalize to uppercase
