from rest_framework import serializers

from apps.lab_orders.models import LabOrder, LabOrderItem


class LabOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for LabOrderItem model - read only."""

    display_name = serializers.CharField(read_only=True)
    lab_test_id = serializers.IntegerField(source="lab_test.id", read_only=True, allow_null=True)
    category_display = serializers.SerializerMethodField()
    sample_type_display = serializers.SerializerMethodField()

    class Meta:
        model = LabOrderItem
        fields = [
            "id",
            "lab_test_id",
            "test_name",
            "test_code",
            "category",
            "category_display",
            "sample_type",
            "sample_type_display",
            "special_instructions",
            "result",
            "result_date",
            "is_abnormal",
            "result_notes",
            "display_name",
        ]
        read_only_fields = ["id"]

    def get_category_display(self, obj):
        """Get display value for category."""
        from apps.lab_orders.models import LabTest
        category_dict = dict(LabTest.CATEGORY_CHOICES)
        return str(category_dict.get(obj.category, obj.category))

    def get_sample_type_display(self, obj):
        """Get display value for sample_type."""
        from apps.lab_orders.models import LabTest
        sample_type_dict = dict(LabTest.SAMPLE_TYPE_CHOICES)
        return str(sample_type_dict.get(obj.sample_type, obj.sample_type))


class LabOrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating LabOrderItem."""

    lab_test_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = LabOrderItem
        fields = [
            "lab_test_id",
            "test_name",
            "test_code",
            "category",
            "sample_type",
            "special_instructions",
        ]


class LabOrderItemResultSerializer(serializers.ModelSerializer):
    """Serializer for updating lab order item results."""

    class Meta:
        model = LabOrderItem
        fields = [
            "result",
            "is_abnormal",
            "result_notes",
        ]


class LabOrderSerializer(serializers.ModelSerializer):
    """Serializer for LabOrder model - read only."""

    items = LabOrderItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(read_only=True)
    doctor_name = serializers.CharField(read_only=True)
    test_count = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    consultation_id_display = serializers.CharField(
        source="consultation.consultation_id", read_only=True
    )

    class Meta:
        model = LabOrder
        fields = [
            "id",
            "order_id",
            "consultation",
            "consultation_id_display",
            "patient",
            "patient_name",
            "ordered_by",
            "doctor_name",
            "order_date",
            "priority",
            "priority_display",
            "clinical_indication",
            "notes",
            "status",
            "status_display",
            "items",
            "test_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "order_id", "created_at", "updated_at"]


class LabOrderCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating LabOrder with nested items."""

    items = LabOrderItemCreateSerializer(many=True)

    class Meta:
        model = LabOrder
        fields = [
            "consultation",
            "order_date",
            "priority",
            "clinical_indication",
            "notes",
            "status",
            "items",
        ]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        request = self.context.get("request")

        # Get clinic and patient from consultation
        consultation = validated_data.get("consultation")
        validated_data["clinic"] = consultation.clinic
        validated_data["patient"] = consultation.patient
        validated_data["ordered_by"] = request.user if request else None

        # Generate order ID
        validated_data["order_id"] = self._generate_order_id(validated_data["clinic"])

        lab_order = LabOrder.objects.create(**validated_data)

        # Create items
        for item_data in items_data:
            lab_test_id = item_data.pop("lab_test_id", None)
            if lab_test_id:
                from apps.lab_orders.models import LabTest
                try:
                    lab_test = LabTest.objects.get(id=lab_test_id)
                    item_data["lab_test"] = lab_test
                    # Auto-fill from lab test if not provided
                    if not item_data.get("test_name"):
                        item_data["test_name"] = lab_test.name
                    if not item_data.get("test_code"):
                        item_data["test_code"] = lab_test.code
                    if not item_data.get("category"):
                        item_data["category"] = lab_test.category
                    if not item_data.get("sample_type"):
                        item_data["sample_type"] = lab_test.sample_type
                except LabTest.DoesNotExist:
                    pass
            LabOrderItem.objects.create(lab_order=lab_order, **item_data)

        return lab_order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        # Update lab order fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update items if provided
        if items_data is not None:
            # Delete existing items
            instance.items.all().delete()

            # Create new items
            for item_data in items_data:
                lab_test_id = item_data.pop("lab_test_id", None)
                if lab_test_id:
                    from apps.lab_orders.models import LabTest
                    try:
                        lab_test = LabTest.objects.get(id=lab_test_id)
                        item_data["lab_test"] = lab_test
                        # Auto-fill from lab test if not provided
                        if not item_data.get("test_name"):
                            item_data["test_name"] = lab_test.name
                        if not item_data.get("test_code"):
                            item_data["test_code"] = lab_test.code
                        if not item_data.get("category"):
                            item_data["category"] = lab_test.category
                        if not item_data.get("sample_type"):
                            item_data["sample_type"] = lab_test.sample_type
                    except LabTest.DoesNotExist:
                        pass
                LabOrderItem.objects.create(lab_order=instance, **item_data)

        return instance

    def _generate_order_id(self, clinic):
        """Generate a unique lab order ID."""
        from datetime import date

        year = date.today().year
        prefix = f"LAB-{year}-"

        # Get the last order ID for this clinic and year
        last_order = (
            LabOrder.objects.filter(
                clinic=clinic,
                order_id__startswith=prefix,
            )
            .order_by("-order_id")
            .first()
        )

        if last_order:
            try:
                last_number = int(last_order.order_id.split("-")[-1])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}{str(new_number).zfill(4)}"
