from rest_framework import serializers

from apps.medicines.models import Medicine


class MedicineSerializer(serializers.ModelSerializer):
    """Serializer for Medicine model."""

    form_display = serializers.CharField(source="get_form_display", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    display_name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Medicine
        fields = [
            "id",
            "generic_name",
            "brand_name",
            "strength",
            "form",
            "form_display",
            "category",
            "category_display",
            "default_sig",
            "default_quantity",
            "notes",
            "is_active",
            "display_name",
            "full_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        # Get clinic from request context
        request = self.context.get("request")
        if request and hasattr(request.user, "clinic"):
            validated_data["clinic"] = request.user.clinic
        return super().create(validated_data)
