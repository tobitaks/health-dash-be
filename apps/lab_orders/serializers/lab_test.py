from rest_framework import serializers

from apps.lab_orders.models import LabTest


class LabTestSerializer(serializers.ModelSerializer):
    """Serializer for LabTest model - read only."""

    display_name = serializers.CharField(read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    sample_type_display = serializers.CharField(source="get_sample_type_display", read_only=True)

    class Meta:
        model = LabTest
        fields = [
            "id",
            "name",
            "code",
            "category",
            "category_display",
            "sample_type",
            "sample_type_display",
            "description",
            "turnaround_time",
            "price",
            "special_instructions",
            "is_active",
            "display_name",
        ]
        read_only_fields = ["id"]


class LabTestCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating LabTest."""

    class Meta:
        model = LabTest
        fields = [
            "name",
            "code",
            "category",
            "sample_type",
            "description",
            "turnaround_time",
            "price",
            "special_instructions",
            "is_active",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        # Get clinic from request
        if hasattr(request, "clinic"):
            validated_data["clinic"] = request.clinic
        return super().create(validated_data)
