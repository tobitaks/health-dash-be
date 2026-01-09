"""
Unit tests for the billing app.
"""

from datetime import date
from decimal import Decimal

from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from rest_framework import serializers
from rest_framework.request import Request

from apps.billing.models import Invoice, InvoiceItem
from apps.billing.serializers import (
    InvoiceCancelSerializer,
    InvoiceCreateUpdateSerializer,
    InvoiceFinalizeSerializer,
    InvoiceItemSerializer,
    InvoicePaySerializer,
    InvoiceSerializer,
)
from apps.clinic.models import Clinic, Service
from apps.consultations.models import Consultation
from apps.patients.models import Patient
from apps.users.models import CustomUser


class InvoiceModelTestCase(TestCase):
    """Tests for the Invoice model."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            clinic=self.clinic,
        )
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1990, 1, 15),
            gender="female",
            phone="+63 912 345 6789",
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            created_by=self.user,
            chief_complaint="General checkup",
            consultation_id="CON-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
            status="completed",
        )
        self.invoice = Invoice.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            created_by=self.user,
            invoice_id="INV-2026-0001",
            invoice_date=date.today(),
            subtotal=Decimal("1000.00"),
            total=Decimal("1000.00"),
            status="draft",
        )

    def test_invoice_creation(self):
        """Invoice should be created with required fields."""
        self.assertEqual(self.invoice.invoice_id, "INV-2026-0001")
        self.assertEqual(self.invoice.clinic, self.clinic)
        self.assertEqual(self.invoice.patient, self.patient)
        self.assertEqual(self.invoice.status, "draft")

    def test_invoice_str(self):
        """Invoice __str__ should return invoice_id and patient."""
        expected = "INV-2026-0001 - PT-2026-0001 - Jane Smith"
        self.assertEqual(str(self.invoice), expected)

    def test_invoice_defaults(self):
        """Invoice should have sensible defaults."""
        consultation2 = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            created_by=self.user,
            chief_complaint="General checkup",
            consultation_id="CON-2026-0002",
            consultation_date=date.today(),
            consultation_time="11:00:00",
        )
        invoice = Invoice.objects.create(
            clinic=self.clinic,
            consultation=consultation2,
            patient=self.patient,
            invoice_id="INV-2026-0002",
            invoice_date=date.today(),
        )
        self.assertEqual(invoice.subtotal, Decimal("0.00"))
        self.assertEqual(invoice.discount_type, "none")
        self.assertEqual(invoice.discount_value, Decimal("0.00"))
        self.assertEqual(invoice.discount_amount, Decimal("0.00"))
        self.assertEqual(invoice.total, Decimal("0.00"))
        self.assertEqual(invoice.amount_paid, Decimal("0.00"))
        self.assertEqual(invoice.status, "draft")
        self.assertEqual(invoice.payment_method, "cash")

    def test_invoice_unique_together(self):
        """Same invoice_id in same clinic should raise IntegrityError."""
        consultation2 = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            created_by=self.user,
            chief_complaint="General checkup",
            consultation_id="CON-2026-0003",
            consultation_date=date.today(),
            consultation_time="12:00:00",
        )
        with self.assertRaises(IntegrityError):
            Invoice.objects.create(
                clinic=self.clinic,
                consultation=consultation2,
                patient=self.patient,
                invoice_id="INV-2026-0001",  # Duplicate
                invoice_date=date.today(),
            )

    def test_invoice_same_id_different_clinic(self):
        """Same invoice_id in different clinic should be allowed."""
        clinic2 = Clinic.objects.create(name="Another Clinic")
        patient2 = Patient.objects.create(
            clinic=clinic2,
            patient_id="PT-2026-0001",
            first_name="Bob",
            last_name="Jones",
            date_of_birth=date(1985, 5, 20),
            gender="male",
            phone="+63 912 345 6780",
        )
        consultation2 = Consultation.objects.create(
            clinic=clinic2,
            patient=patient2,
            consultation_id="CON-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
            chief_complaint="General checkup",
        )
        invoice = Invoice.objects.create(
            clinic=clinic2,
            consultation=consultation2,
            patient=patient2,
            invoice_id="INV-2026-0001",  # Same ID, different clinic
            invoice_date=date.today(),
        )
        self.assertEqual(invoice.invoice_id, "INV-2026-0001")
        self.assertNotEqual(invoice.clinic, self.clinic)

    def test_patient_name_property(self):
        """patient_name should return patient's full name."""
        self.assertEqual(self.invoice.patient_name, "Jane Smith")

    def test_created_by_name_property(self):
        """created_by_name should return creator's name."""
        self.assertEqual(self.invoice.created_by_name, "John Doe")

    def test_created_by_name_without_name(self):
        """created_by_name should return email if no name."""
        user = CustomUser.objects.create_user(
            username="noname",
            email="noname@example.com",
            password="testpass123",
            clinic=self.clinic,
        )
        self.invoice.created_by = user
        self.invoice.save()
        self.assertEqual(self.invoice.created_by_name, "noname@example.com")

    def test_created_by_name_none(self):
        """created_by_name should handle None creator."""
        self.invoice.created_by = None
        self.invoice.save()
        self.assertEqual(self.invoice.created_by_name, "")

    def test_item_count_property(self):
        """item_count should return number of items."""
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Consultation",
            quantity=1,
            unit_price=Decimal("500.00"),
            amount=Decimal("500.00"),
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Lab Test",
            quantity=2,
            unit_price=Decimal("250.00"),
            amount=Decimal("500.00"),
        )
        self.assertEqual(self.invoice.item_count, 2)

    def test_balance_property(self):
        """balance should return total - amount_paid."""
        self.invoice.total = Decimal("1000.00")
        self.invoice.amount_paid = Decimal("300.00")
        self.invoice.save()
        self.assertEqual(self.invoice.balance, Decimal("700.00"))

    def test_balance_fully_paid(self):
        """balance should be zero when fully paid."""
        self.invoice.total = Decimal("1000.00")
        self.invoice.amount_paid = Decimal("1000.00")
        self.invoice.save()
        self.assertEqual(self.invoice.balance, Decimal("0.00"))

    def test_calculate_totals_no_discount(self):
        """calculate_totals should sum items without discount."""
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Service 1",
            quantity=1,
            unit_price=Decimal("500.00"),
            amount=Decimal("500.00"),
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Service 2",
            quantity=2,
            unit_price=Decimal("200.00"),
            amount=Decimal("400.00"),
        )
        self.invoice.discount_type = "none"
        self.invoice.calculate_totals()

        self.assertEqual(self.invoice.subtotal, Decimal("900.00"))
        self.assertEqual(self.invoice.discount_amount, Decimal("0.00"))
        self.assertEqual(self.invoice.total, Decimal("900.00"))

    def test_calculate_totals_percent_discount(self):
        """calculate_totals should apply percentage discount."""
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Service",
            quantity=1,
            unit_price=Decimal("1000.00"),
            amount=Decimal("1000.00"),
        )
        self.invoice.discount_type = "percent"
        self.invoice.discount_value = Decimal("10.00")  # 10%
        self.invoice.calculate_totals()

        self.assertEqual(self.invoice.subtotal, Decimal("1000.00"))
        self.assertEqual(self.invoice.discount_amount, Decimal("100.00"))
        self.assertEqual(self.invoice.total, Decimal("900.00"))

    def test_calculate_totals_amount_discount(self):
        """calculate_totals should apply fixed amount discount."""
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Service",
            quantity=1,
            unit_price=Decimal("1000.00"),
            amount=Decimal("1000.00"),
        )
        self.invoice.discount_type = "amount"
        self.invoice.discount_value = Decimal("150.00")
        self.invoice.calculate_totals()

        self.assertEqual(self.invoice.subtotal, Decimal("1000.00"))
        self.assertEqual(self.invoice.discount_amount, Decimal("150.00"))
        self.assertEqual(self.invoice.total, Decimal("850.00"))

    def test_status_choices(self):
        """All status choices should be valid."""
        valid_statuses = ["draft", "pending", "paid", "cancelled"]
        for status in valid_statuses:
            self.invoice.status = status
            self.invoice.save()
            self.assertEqual(self.invoice.status, status)

    def test_discount_type_choices(self):
        """All discount type choices should be valid."""
        valid_types = ["none", "amount", "percent"]
        for dtype in valid_types:
            self.invoice.discount_type = dtype
            self.invoice.save()
            self.assertEqual(self.invoice.discount_type, dtype)


class InvoiceItemModelTestCase(TestCase):
    """Tests for the InvoiceItem model."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1990, 1, 15),
            gender="female",
            phone="+63 912 345 6789",
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            consultation_id="CON-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
            chief_complaint="General checkup",
        )
        self.invoice = Invoice.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            invoice_id="INV-2026-0001",
            invoice_date=date.today(),
        )
        self.service = Service.objects.create(
            clinic=self.clinic,
            name="Consultation",
            code="CON001",
            price=Decimal("500.00"),
        )
        self.item = InvoiceItem.objects.create(
            invoice=self.invoice,
            service=self.service,
            description="General Consultation",
            quantity=1,
            unit_price=Decimal("500.00"),
            amount=Decimal("500.00"),
        )

    def test_item_creation(self):
        """InvoiceItem should be created with required fields."""
        self.assertEqual(self.item.description, "General Consultation")
        self.assertEqual(self.item.quantity, 1)
        self.assertEqual(self.item.unit_price, Decimal("500.00"))
        self.assertEqual(self.item.amount, Decimal("500.00"))

    def test_item_str(self):
        """InvoiceItem __str__ should return description and amount."""
        expected = "General Consultation - 500.00"
        self.assertEqual(str(self.item), expected)

    def test_item_auto_calculate_amount(self):
        """InvoiceItem.save() should auto-calculate amount."""
        item = InvoiceItem(
            invoice=self.invoice,
            description="Lab Test",
            quantity=3,
            unit_price=Decimal("150.00"),
            amount=Decimal("0.00"),  # Will be calculated
        )
        item.save()
        self.assertEqual(item.amount, Decimal("450.00"))

    def test_item_update_recalculates_amount(self):
        """Updating quantity/price should recalculate amount."""
        self.item.quantity = 2
        self.item.unit_price = Decimal("300.00")
        self.item.save()
        self.assertEqual(self.item.amount, Decimal("600.00"))

    def test_item_with_service_reference(self):
        """InvoiceItem can reference a service."""
        self.assertEqual(self.item.service, self.service)

    def test_item_without_service(self):
        """InvoiceItem can exist without service reference."""
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Custom Service",
            quantity=1,
            unit_price=Decimal("100.00"),
            amount=Decimal("100.00"),
        )
        self.assertIsNone(item.service)

    def test_item_cascade_delete(self):
        """Deleting invoice should delete items."""
        item_id = self.item.id
        self.invoice.delete()
        self.assertFalse(InvoiceItem.objects.filter(id=item_id).exists())


class InvoiceSerializerTestCase(TestCase):
    """Tests for the InvoiceSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            clinic=self.clinic,
        )
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1990, 1, 15),
            gender="female",
            phone="+63 912 345 6789",
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            created_by=self.user,
            chief_complaint="General checkup",
            consultation_id="CON-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
        )
        self.invoice = Invoice.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            created_by=self.user,
            invoice_id="INV-2026-0001",
            invoice_date=date.today(),
            subtotal=Decimal("1000.00"),
            total=Decimal("1000.00"),
            status="pending",
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Consultation",
            quantity=1,
            unit_price=Decimal("1000.00"),
            amount=Decimal("1000.00"),
        )

    def test_serializer_contains_expected_fields(self):
        """Serializer should contain all expected fields."""
        serializer = InvoiceSerializer(self.invoice)
        data = serializer.data

        expected_fields = [
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
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_data_values(self):
        """Serializer should return correct values."""
        serializer = InvoiceSerializer(self.invoice)
        data = serializer.data

        self.assertEqual(data["invoice_id"], "INV-2026-0001")
        self.assertEqual(data["patient_name"], "Jane Smith")
        self.assertEqual(data["created_by_name"], "John Doe")
        self.assertEqual(Decimal(data["subtotal"]), Decimal("1000.00"))
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["status_display"], "Pending")

    def test_serializer_items_included(self):
        """Serializer should include nested items."""
        serializer = InvoiceSerializer(self.invoice)
        items = serializer.data["items"]

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["description"], "Consultation")
        self.assertEqual(Decimal(items[0]["amount"]), Decimal("1000.00"))

    def test_serializer_item_count(self):
        """item_count should be included."""
        serializer = InvoiceSerializer(self.invoice)
        self.assertEqual(serializer.data["item_count"], 1)

    def test_serializer_balance(self):
        """balance should be calculated correctly."""
        serializer = InvoiceSerializer(self.invoice)
        self.assertEqual(Decimal(serializer.data["balance"]), Decimal("1000.00"))


class InvoiceItemSerializerTestCase(TestCase):
    """Tests for the InvoiceItemSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1990, 1, 15),
            gender="female",
            phone="+63 912 345 6789",
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            consultation_id="CON-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
            chief_complaint="General checkup",
        )
        self.invoice = Invoice.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            invoice_id="INV-2026-0001",
            invoice_date=date.today(),
        )
        self.service = Service.objects.create(
            clinic=self.clinic,
            name="Consultation",
            code="CON001",
            price=Decimal("500.00"),
        )
        self.item = InvoiceItem.objects.create(
            invoice=self.invoice,
            service=self.service,
            description="General Consultation",
            quantity=2,
            unit_price=Decimal("500.00"),
            amount=Decimal("1000.00"),
        )

    def test_serializer_fields(self):
        """InvoiceItemSerializer should contain expected fields."""
        serializer = InvoiceItemSerializer(self.item)
        data = serializer.data

        expected_fields = ["id", "service_id", "description", "quantity", "unit_price", "amount"]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_values(self):
        """InvoiceItemSerializer should return correct values."""
        serializer = InvoiceItemSerializer(self.item)
        data = serializer.data

        self.assertEqual(data["description"], "General Consultation")
        self.assertEqual(data["quantity"], 2)
        self.assertEqual(Decimal(data["unit_price"]), Decimal("500.00"))
        self.assertEqual(Decimal(data["amount"]), Decimal("1000.00"))
        self.assertEqual(data["service_id"], self.service.id)


class InvoiceCreateUpdateSerializerTestCase(TestCase):
    """Tests for the InvoiceCreateUpdateSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            clinic=self.clinic,
        )
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1990, 1, 15),
            gender="female",
            phone="+63 912 345 6789",
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            created_by=self.user,
            chief_complaint="General checkup",
            consultation_id="CON-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
        )
        self.service = Service.objects.create(
            clinic=self.clinic,
            name="Consultation",
            code="CON001",
            price=Decimal("500.00"),
        )
        self.valid_data = {
            "consultation": self.consultation.id,
            "invoice_date": date.today().isoformat(),
            "discount_type": "none",
            "discount_value": "0.00",
            "items": [
                {
                    "description": "Consultation Fee",
                    "quantity": 1,
                    "unit_price": "500.00",
                }
            ],
        }

    def get_mock_request(self):
        """Create a mock request with user context."""
        request = self.factory.get("/")
        request.user = self.user
        drf_request = Request(request)
        drf_request.user = self.user
        return drf_request

    def test_valid_data_is_valid(self):
        """Serializer should validate with valid data."""
        serializer = InvoiceCreateUpdateSerializer(data=self.valid_data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_invoice_with_items(self):
        """Serializer should create invoice with items."""
        serializer = InvoiceCreateUpdateSerializer(data=self.valid_data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        invoice = serializer.save()

        self.assertEqual(invoice.clinic, self.clinic)
        self.assertEqual(invoice.patient, self.patient)
        self.assertEqual(invoice.created_by, self.user)
        self.assertEqual(invoice.items.count(), 1)

    def test_create_generates_invoice_id(self):
        """Serializer should generate invoice_id."""
        serializer = InvoiceCreateUpdateSerializer(data=self.valid_data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        invoice = serializer.save()

        self.assertRegex(invoice.invoice_id, r"^INV-\d{4}-\d{4}$")

    def test_create_calculates_totals(self):
        """Serializer should calculate totals."""
        data = self.valid_data.copy()
        data["items"] = [
            {"description": "Service 1", "quantity": 2, "unit_price": "100.00"},
            {"description": "Service 2", "quantity": 1, "unit_price": "300.00"},
        ]
        serializer = InvoiceCreateUpdateSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        invoice = serializer.save()

        self.assertEqual(invoice.subtotal, Decimal("500.00"))
        self.assertEqual(invoice.total, Decimal("500.00"))

    def test_create_with_percent_discount(self):
        """Serializer should apply percentage discount."""
        data = self.valid_data.copy()
        data["discount_type"] = "percent"
        data["discount_value"] = "20.00"  # 20%
        data["items"] = [
            {"description": "Service", "quantity": 1, "unit_price": "1000.00"},
        ]
        serializer = InvoiceCreateUpdateSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        invoice = serializer.save()

        self.assertEqual(invoice.subtotal, Decimal("1000.00"))
        self.assertEqual(invoice.discount_amount, Decimal("200.00"))
        self.assertEqual(invoice.total, Decimal("800.00"))

    def test_create_with_service_id(self):
        """Serializer should link item to service."""
        data = self.valid_data.copy()
        data["items"] = [
            {
                "service_id": self.service.id,
                "description": "Consultation",
                "quantity": 1,
                "unit_price": "500.00",
            }
        ]
        serializer = InvoiceCreateUpdateSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        invoice = serializer.save()

        item = invoice.items.first()
        self.assertEqual(item.service, self.service)

    def test_update_invoice(self):
        """Serializer should update invoice."""
        invoice = Invoice.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            invoice_id="INV-2026-0001",
            invoice_date=date.today(),
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description="Old Item",
            quantity=1,
            unit_price=Decimal("100.00"),
            amount=Decimal("100.00"),
        )

        update_data = {
            "consultation": self.consultation.id,
            "invoice_date": date.today().isoformat(),
            "discount_type": "amount",
            "discount_value": "50.00",
            "notes": "Updated notes",
            "items": [
                {"description": "New Item", "quantity": 2, "unit_price": "200.00"},
            ],
        }
        serializer = InvoiceCreateUpdateSerializer(
            invoice, data=update_data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.notes, "Updated notes")
        self.assertEqual(updated.discount_type, "amount")
        self.assertEqual(updated.items.count(), 1)
        self.assertEqual(updated.items.first().description, "New Item")


class InvoicePaySerializerTestCase(TestCase):
    """Tests for the InvoicePaySerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1990, 1, 15),
            gender="female",
            phone="+63 912 345 6789",
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            consultation_id="CON-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
            chief_complaint="General checkup",
        )
        self.invoice = Invoice.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            invoice_id="INV-2026-0001",
            invoice_date=date.today(),
            total=Decimal("1000.00"),
            status="pending",
        )

    def test_pay_pending_invoice(self):
        """Should pay pending invoice."""
        serializer = InvoicePaySerializer(self.invoice, data={})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        paid = serializer.save()

        self.assertEqual(paid.status, "paid")
        self.assertEqual(paid.amount_paid, Decimal("1000.00"))
        self.assertIsNotNone(paid.payment_date)
        self.assertEqual(paid.payment_method, "cash")

    def test_pay_draft_invoice(self):
        """Should pay draft invoice."""
        self.invoice.status = "draft"
        self.invoice.save()

        serializer = InvoicePaySerializer(self.invoice, data={})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        paid = serializer.save()

        self.assertEqual(paid.status, "paid")

    def test_pay_with_reference(self):
        """Should record payment reference."""
        serializer = InvoicePaySerializer(self.invoice, data={"payment_reference": "REC-001"})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        paid = serializer.save()

        self.assertEqual(paid.payment_reference, "REC-001")

    def test_cannot_pay_paid_invoice(self):
        """Should not pay already paid invoice."""
        self.invoice.status = "paid"
        self.invoice.save()

        serializer = InvoicePaySerializer(self.invoice, data={})
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(serializers.ValidationError):
            serializer.save()

    def test_cannot_pay_cancelled_invoice(self):
        """Should not pay cancelled invoice."""
        self.invoice.status = "cancelled"
        self.invoice.save()

        serializer = InvoicePaySerializer(self.invoice, data={})
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(serializers.ValidationError):
            serializer.save()


class InvoiceFinalizeSerializerTestCase(TestCase):
    """Tests for the InvoiceFinalizeSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1990, 1, 15),
            gender="female",
            phone="+63 912 345 6789",
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            consultation_id="CON-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
            chief_complaint="General checkup",
        )
        self.invoice = Invoice.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            invoice_id="INV-2026-0001",
            invoice_date=date.today(),
            status="draft",
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Service",
            quantity=1,
            unit_price=Decimal("500.00"),
            amount=Decimal("500.00"),
        )

    def test_finalize_draft_invoice(self):
        """Should finalize draft invoice."""
        serializer = InvoiceFinalizeSerializer(self.invoice, data={})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        finalized = serializer.save()

        self.assertEqual(finalized.status, "pending")

    def test_cannot_finalize_pending_invoice(self):
        """Should not finalize non-draft invoice."""
        self.invoice.status = "pending"
        self.invoice.save()

        serializer = InvoiceFinalizeSerializer(self.invoice, data={})
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(serializers.ValidationError):
            serializer.save()

    def test_cannot_finalize_without_items(self):
        """Should not finalize invoice without items."""
        self.invoice.items.all().delete()

        serializer = InvoiceFinalizeSerializer(self.invoice, data={})
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(serializers.ValidationError):
            serializer.save()


class InvoiceCancelSerializerTestCase(TestCase):
    """Tests for the InvoiceCancelSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1990, 1, 15),
            gender="female",
            phone="+63 912 345 6789",
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            consultation_id="CON-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
            chief_complaint="General checkup",
        )
        self.invoice = Invoice.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            invoice_id="INV-2026-0001",
            invoice_date=date.today(),
            status="pending",
        )

    def test_cancel_pending_invoice(self):
        """Should cancel pending invoice."""
        serializer = InvoiceCancelSerializer(self.invoice, data={})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        cancelled = serializer.save()

        self.assertEqual(cancelled.status, "cancelled")

    def test_cancel_draft_invoice(self):
        """Should cancel draft invoice."""
        self.invoice.status = "draft"
        self.invoice.save()

        serializer = InvoiceCancelSerializer(self.invoice, data={})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        cancelled = serializer.save()

        self.assertEqual(cancelled.status, "cancelled")

    def test_cannot_cancel_paid_invoice(self):
        """Should not cancel paid invoice."""
        self.invoice.status = "paid"
        self.invoice.save()

        serializer = InvoiceCancelSerializer(self.invoice, data={})
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(serializers.ValidationError):
            serializer.save()

    def test_cannot_cancel_already_cancelled(self):
        """Should not cancel already cancelled invoice."""
        self.invoice.status = "cancelled"
        self.invoice.save()

        serializer = InvoiceCancelSerializer(self.invoice, data={})
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(serializers.ValidationError):
            serializer.save()
