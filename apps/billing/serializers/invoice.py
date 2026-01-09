import contextlib
from decimal import Decimal

from rest_framework import serializers

from apps.billing.models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for InvoiceItem model - read only."""

    service_id = serializers.IntegerField(source="service.id", read_only=True, allow_null=True)

    class Meta:
        model = InvoiceItem
        fields = [
            "id",
            "service_id",
            "description",
            "quantity",
            "unit_price",
            "amount",
        ]
        read_only_fields = ["id", "amount"]


class InvoiceItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating InvoiceItem."""

    service_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = InvoiceItem
        fields = [
            "service_id",
            "description",
            "quantity",
            "unit_price",
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model - read only."""

    items = InvoiceItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(read_only=True)
    created_by_name = serializers.CharField(read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    discount_type_display = serializers.CharField(source="get_discount_type_display", read_only=True)
    consultation_id_display = serializers.CharField(source="consultation.consultation_id", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_id",
            "consultation",
            "consultation_id_display",
            "patient",
            "patient_name",
            "created_by",
            "created_by_name",
            "invoice_date",
            "subtotal",
            "discount_type",
            "discount_type_display",
            "discount_value",
            "discount_amount",
            "total",
            "amount_paid",
            "payment_date",
            "payment_method",
            "payment_reference",
            "balance",
            "status",
            "status_display",
            "notes",
            "items",
            "item_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "invoice_id", "created_at", "updated_at"]


class InvoiceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Invoice with nested items."""

    items = InvoiceItemCreateSerializer(many=True)

    class Meta:
        model = Invoice
        fields = [
            "consultation",
            "invoice_date",
            "discount_type",
            "discount_value",
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
        validated_data["created_by"] = request.user if request else None

        # Generate invoice ID
        validated_data["invoice_id"] = self._generate_invoice_id(validated_data["clinic"])

        # Create invoice
        invoice = Invoice.objects.create(**validated_data)

        # Create items
        for item_data in items_data:
            service_id = item_data.pop("service_id", None)
            if service_id:
                from apps.clinic.models import Service

                with contextlib.suppress(Service.DoesNotExist):
                    item_data["service"] = Service.objects.get(id=service_id)
            # Calculate amount
            quantity = item_data.get("quantity", 1)
            unit_price = item_data.get("unit_price", Decimal("0.00"))
            item_data["amount"] = Decimal(str(quantity)) * unit_price
            InvoiceItem.objects.create(invoice=invoice, **item_data)

        # Calculate totals
        invoice.calculate_totals()
        invoice.save()

        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update items if provided
        if items_data is not None:
            # Delete existing items
            instance.items.all().delete()

            # Create new items
            for item_data in items_data:
                service_id = item_data.pop("service_id", None)
                if service_id:
                    from apps.clinic.models import Service

                    with contextlib.suppress(Service.DoesNotExist):
                        item_data["service"] = Service.objects.get(id=service_id)
                # Calculate amount
                quantity = item_data.get("quantity", 1)
                unit_price = item_data.get("unit_price", Decimal("0.00"))
                item_data["amount"] = Decimal(str(quantity)) * unit_price
                InvoiceItem.objects.create(invoice=instance, **item_data)

            # Recalculate totals
            instance.calculate_totals()
            instance.save()

        return instance

    def _generate_invoice_id(self, clinic):
        """Generate a unique invoice ID."""
        from datetime import date

        year = date.today().year
        prefix = f"INV-{year}-"

        # Get the last invoice ID for this clinic and year
        last_invoice = (
            Invoice.objects.filter(
                clinic=clinic,
                invoice_id__startswith=prefix,
            )
            .order_by("-invoice_id")
            .first()
        )

        if last_invoice:
            try:
                last_number = int(last_invoice.invoice_id.split("-")[-1])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}{str(new_number).zfill(4)}"


class InvoicePaySerializer(serializers.Serializer):
    """Serializer for recording payment."""

    payment_reference = serializers.CharField(required=False, allow_blank=True, default="")

    def update(self, instance, validated_data):
        from django.utils import timezone

        if instance.status not in ["draft", "pending"]:
            raise serializers.ValidationError("Only draft or pending invoices can be paid.")

        instance.amount_paid = instance.total
        instance.payment_date = timezone.now()
        instance.payment_method = "cash"
        instance.payment_reference = validated_data.get("payment_reference", "")
        instance.status = "paid"
        instance.save()

        return instance


class InvoiceFinalizeSerializer(serializers.Serializer):
    """Serializer for finalizing (moving from draft to pending)."""

    def update(self, instance, validated_data):
        if instance.status != "draft":
            raise serializers.ValidationError("Only draft invoices can be finalized.")

        if instance.items.count() == 0:
            raise serializers.ValidationError("Invoice must have at least one item.")

        instance.status = "pending"
        instance.save()

        return instance


class InvoiceCancelSerializer(serializers.Serializer):
    """Serializer for cancelling invoice."""

    def update(self, instance, validated_data):
        if instance.status == "paid":
            raise serializers.ValidationError("Paid invoices cannot be cancelled.")
        if instance.status == "cancelled":
            raise serializers.ValidationError("Invoice is already cancelled.")

        instance.status = "cancelled"
        instance.save()

        return instance
