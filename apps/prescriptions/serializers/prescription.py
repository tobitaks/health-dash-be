import contextlib

from rest_framework import serializers

from apps.prescriptions.models import Prescription, PrescriptionItem


class PrescriptionItemSerializer(serializers.ModelSerializer):
    """Serializer for PrescriptionItem model."""

    display_name = serializers.CharField(read_only=True)
    medicine_id = serializers.IntegerField(source="medicine.id", read_only=True, allow_null=True)

    class Meta:
        model = PrescriptionItem
        fields = [
            "id",
            "medicine_id",
            "medicine_name",
            "strength",
            "form",
            "sig",
            "quantity",
            "notes",
            "display_name",
        ]
        read_only_fields = ["id"]


class PrescriptionItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating PrescriptionItem."""

    medicine_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = PrescriptionItem
        fields = [
            "medicine_id",
            "medicine_name",
            "strength",
            "form",
            "sig",
            "quantity",
            "notes",
        ]


class PrescriptionSerializer(serializers.ModelSerializer):
    """Serializer for Prescription model - read only."""

    items = PrescriptionItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(read_only=True)
    doctor_name = serializers.CharField(read_only=True)
    medicine_count = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    consultation_id_display = serializers.CharField(source="consultation.consultation_id", read_only=True)

    class Meta:
        model = Prescription
        fields = [
            "id",
            "prescription_id",
            "consultation",
            "consultation_id_display",
            "patient",
            "patient_name",
            "prescribed_by",
            "doctor_name",
            "prescription_date",
            "notes",
            "status",
            "status_display",
            "items",
            "medicine_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "prescription_id", "created_at", "updated_at"]


class PrescriptionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Prescription with nested items."""

    items = PrescriptionItemCreateSerializer(many=True)

    class Meta:
        model = Prescription
        fields = [
            "consultation",
            "prescription_date",
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
        validated_data["prescribed_by"] = request.user if request else None

        # Generate prescription ID
        validated_data["prescription_id"] = self._generate_prescription_id(validated_data["clinic"])

        prescription = Prescription.objects.create(**validated_data)

        # Create items
        for item_data in items_data:
            medicine_id = item_data.pop("medicine_id", None)
            if medicine_id:
                from apps.medicines.models import Medicine

                with contextlib.suppress(Medicine.DoesNotExist):
                    item_data["medicine"] = Medicine.objects.get(id=medicine_id)
            PrescriptionItem.objects.create(prescription=prescription, **item_data)

        return prescription

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        # Update prescription fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update items if provided
        if items_data is not None:
            # Delete existing items
            instance.items.all().delete()

            # Create new items
            for item_data in items_data:
                medicine_id = item_data.pop("medicine_id", None)
                if medicine_id:
                    from apps.medicines.models import Medicine

                    with contextlib.suppress(Medicine.DoesNotExist):
                        item_data["medicine"] = Medicine.objects.get(id=medicine_id)
                PrescriptionItem.objects.create(prescription=instance, **item_data)

        return instance

    def _generate_prescription_id(self, clinic):
        """Generate a unique prescription ID."""
        from datetime import date

        year = date.today().year
        prefix = f"RX-{year}-"

        # Get the last prescription ID for this clinic and year
        last_prescription = (
            Prescription.objects.filter(
                clinic=clinic,
                prescription_id__startswith=prefix,
            )
            .order_by("-prescription_id")
            .first()
        )

        if last_prescription:
            try:
                last_number = int(last_prescription.prescription_id.split("-")[-1])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}{str(new_number).zfill(4)}"
