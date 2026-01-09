"""
Unit tests for the lab_orders app.
"""

from datetime import date
from decimal import Decimal

from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from apps.clinic.models import Clinic
from apps.consultations.models import Consultation
from apps.lab_orders.models import LabOrder, LabOrderItem, LabTest
from apps.lab_orders.serializers import (
    LabOrderCreateUpdateSerializer,
    LabOrderItemSerializer,
    LabOrderSerializer,
    LabTestCreateUpdateSerializer,
    LabTestSerializer,
)
from apps.patients.models import Patient
from apps.users.models import CustomUser


class LabTestModelTestCase(TestCase):
    """Tests for the LabTest model."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.lab_test = LabTest.objects.create(
            clinic=self.clinic,
            name="Complete Blood Count",
            code="CBC",
            category="hematology",
            sample_type="blood",
            price=Decimal("500.00"),
            turnaround_time="24-48 hours",
        )

    def test_lab_test_creation(self):
        """LabTest should be created with required fields."""
        self.assertEqual(self.lab_test.name, "Complete Blood Count")
        self.assertEqual(self.lab_test.code, "CBC")
        self.assertEqual(self.lab_test.category, "hematology")
        self.assertEqual(self.lab_test.sample_type, "blood")

    def test_lab_test_str_with_code(self):
        """LabTest __str__ should include code if present."""
        self.assertEqual(str(self.lab_test), "Complete Blood Count (CBC)")

    def test_lab_test_str_without_code(self):
        """LabTest __str__ should work without code."""
        lab_test = LabTest.objects.create(
            clinic=self.clinic,
            name="X-Ray",
            category="imaging",
            sample_type="none",
        )
        self.assertEqual(str(lab_test), "X-Ray")

    def test_lab_test_defaults(self):
        """LabTest should have sensible defaults."""
        lab_test = LabTest.objects.create(
            clinic=self.clinic,
            name="Basic Test",
        )
        self.assertEqual(lab_test.code, "")
        self.assertEqual(lab_test.category, "other")
        self.assertEqual(lab_test.sample_type, "blood")
        self.assertEqual(lab_test.description, "")
        self.assertTrue(lab_test.is_active)

    def test_display_name_property_with_code(self):
        """display_name should include code if present."""
        self.assertEqual(self.lab_test.display_name, "Complete Blood Count (CBC)")

    def test_display_name_property_without_code(self):
        """display_name should work without code."""
        lab_test = LabTest.objects.create(
            clinic=self.clinic,
            name="Simple Test",
            category="chemistry",
        )
        self.assertEqual(lab_test.display_name, "Simple Test")

    def test_lab_test_unique_together_constraint(self):
        """Same name in same clinic should raise IntegrityError."""
        with self.assertRaises(IntegrityError):
            LabTest.objects.create(
                clinic=self.clinic,
                name="Complete Blood Count",  # Duplicate
                category="hematology",
            )

    def test_lab_test_same_name_different_clinic(self):
        """Same name in different clinic should be allowed."""
        clinic2 = Clinic.objects.create(name="Another Clinic")
        lab_test2 = LabTest.objects.create(
            clinic=clinic2,
            name="Complete Blood Count",  # Same name, different clinic
            category="hematology",
        )
        self.assertEqual(lab_test2.name, "Complete Blood Count")
        self.assertNotEqual(lab_test2.clinic, self.clinic)

    def test_category_choices(self):
        """All valid category choices should be accepted."""
        categories = [
            "hematology",
            "chemistry",
            "urinalysis",
            "microbiology",
            "imaging",
            "cardiology",
            "other",
        ]
        for i, category in enumerate(categories):
            lab_test = LabTest.objects.create(
                clinic=self.clinic,
                name=f"Test {i}",
                category=category,
            )
            self.assertEqual(lab_test.category, category)

    def test_sample_type_choices(self):
        """All valid sample_type choices should be accepted."""
        sample_types = [
            "blood",
            "urine",
            "stool",
            "swab",
            "tissue",
            "sputum",
            "csf",
            "none",
            "other",
        ]
        for i, sample_type in enumerate(sample_types):
            lab_test = LabTest.objects.create(
                clinic=self.clinic,
                name=f"Sample Test {i}",
                sample_type=sample_type,
            )
            self.assertEqual(lab_test.sample_type, sample_type)


class LabOrderModelTestCase(TestCase):
    """Tests for the LabOrder model."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-15",
            gender="Male",
            phone="09171234567",
        )
        self.user = CustomUser.objects.create_user(
            username="doctor",
            email="doctor@example.com",
            password="testpass123",
            first_name="Dr. Jane",
            last_name="Smith",
            clinic=self.clinic,
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            created_by=self.user,
            consultation_id="CONS-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
        )
        self.lab_order = LabOrder.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            ordered_by=self.user,
            order_id="LAB-2026-0001",
            order_date=date.today(),
            priority="routine",
            clinical_indication="Annual checkup",
        )

    def test_lab_order_creation(self):
        """LabOrder should be created with required fields."""
        self.assertEqual(self.lab_order.order_id, "LAB-2026-0001")
        self.assertEqual(self.lab_order.patient, self.patient)
        self.assertEqual(self.lab_order.priority, "routine")
        self.assertEqual(self.lab_order.status, "ordered")

    def test_lab_order_str(self):
        """LabOrder __str__ should return order ID and patient."""
        expected = f"LAB-2026-0001 - {self.patient}"
        self.assertEqual(str(self.lab_order), expected)

    def test_lab_order_default_status(self):
        """LabOrder status should default to 'ordered'."""
        self.assertEqual(self.lab_order.status, "ordered")

    def test_lab_order_default_priority(self):
        """LabOrder priority should default to 'routine'."""
        lab_order = LabOrder.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            order_id="LAB-2026-0002",
            order_date=date.today(),
        )
        self.assertEqual(lab_order.priority, "routine")

    def test_lab_order_status_choices(self):
        """All valid status choices should be accepted."""
        statuses = [
            "ordered",
            "collected",
            "processing",
            "results_available",
            "reviewed",
            "cancelled",
        ]
        for i, status in enumerate(statuses):
            lab_order = LabOrder.objects.create(
                clinic=self.clinic,
                consultation=self.consultation,
                patient=self.patient,
                order_id=f"LAB-2026-{100+i:04d}",
                order_date=date.today(),
                status=status,
            )
            self.assertEqual(lab_order.status, status)

    def test_lab_order_priority_choices(self):
        """All valid priority choices should be accepted."""
        priorities = ["routine", "urgent", "stat"]
        for i, priority in enumerate(priorities):
            lab_order = LabOrder.objects.create(
                clinic=self.clinic,
                consultation=self.consultation,
                patient=self.patient,
                order_id=f"LAB-2026-{200+i:04d}",
                order_date=date.today(),
                priority=priority,
            )
            self.assertEqual(lab_order.priority, priority)

    def test_lab_order_unique_together_constraint(self):
        """Same order_id in same clinic should raise IntegrityError."""
        with self.assertRaises(IntegrityError):
            LabOrder.objects.create(
                clinic=self.clinic,
                consultation=self.consultation,
                patient=self.patient,
                order_id="LAB-2026-0001",  # Duplicate
                order_date=date.today(),
            )

    def test_test_count_property(self):
        """test_count should return number of items."""
        self.assertEqual(self.lab_order.test_count, 0)
        LabOrderItem.objects.create(
            lab_order=self.lab_order,
            test_name="CBC",
        )
        self.assertEqual(self.lab_order.test_count, 1)

    def test_patient_name_property(self):
        """patient_name should return patient's full name."""
        self.assertEqual(self.lab_order.patient_name, "John Doe")

    def test_doctor_name_property(self):
        """doctor_name should return ordering doctor's name."""
        self.assertEqual(self.lab_order.doctor_name, "Dr. Jane Smith")

    def test_doctor_name_property_no_doctor(self):
        """doctor_name should return None if no doctor."""
        self.lab_order.ordered_by = None
        self.lab_order.save()
        self.assertIsNone(self.lab_order.doctor_name)


class LabOrderItemModelTestCase(TestCase):
    """Tests for the LabOrderItem model."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-15",
            gender="Male",
            phone="09171234567",
        )
        self.user = CustomUser.objects.create_user(
            username="doctor",
            email="doctor@example.com",
            password="testpass123",
            clinic=self.clinic,
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            created_by=self.user,
            consultation_id="CONS-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
        )
        self.lab_order = LabOrder.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            order_id="LAB-2026-0001",
            order_date=date.today(),
        )
        self.lab_test = LabTest.objects.create(
            clinic=self.clinic,
            name="Complete Blood Count",
            code="CBC",
            category="hematology",
            sample_type="blood",
        )
        self.item = LabOrderItem.objects.create(
            lab_order=self.lab_order,
            lab_test=self.lab_test,
            test_name="Complete Blood Count",
            test_code="CBC",
            category="hematology",
            sample_type="blood",
        )

    def test_lab_order_item_creation(self):
        """LabOrderItem should be created with required fields."""
        self.assertEqual(self.item.test_name, "Complete Blood Count")
        self.assertEqual(self.item.test_code, "CBC")
        self.assertEqual(self.item.category, "hematology")

    def test_lab_order_item_str(self):
        """LabOrderItem __str__ should return test name and order ID."""
        expected = "Complete Blood Count - LAB-2026-0001"
        self.assertEqual(str(self.item), expected)

    def test_display_name_property_with_code(self):
        """display_name should include code if present."""
        self.assertEqual(self.item.display_name, "Complete Blood Count (CBC)")

    def test_display_name_property_without_code(self):
        """display_name should work without code."""
        item = LabOrderItem.objects.create(
            lab_order=self.lab_order,
            test_name="X-Ray",
        )
        self.assertEqual(item.display_name, "X-Ray")

    def test_lab_order_item_defaults(self):
        """LabOrderItem should have sensible defaults."""
        item = LabOrderItem.objects.create(
            lab_order=self.lab_order,
            test_name="Simple Test",
        )
        self.assertEqual(item.test_code, "")
        self.assertEqual(item.category, "")
        self.assertEqual(item.result, "")
        self.assertFalse(item.is_abnormal)
        self.assertIsNone(item.result_date)

    def test_lab_order_item_result_fields(self):
        """Result fields should store correctly."""
        self.item.result = "WBC: 7.5, RBC: 4.8, Hgb: 14.2"
        self.item.is_abnormal = True
        self.item.result_notes = "Slightly elevated WBC"
        self.item.save()
        self.item.refresh_from_db()

        self.assertEqual(self.item.result, "WBC: 7.5, RBC: 4.8, Hgb: 14.2")
        self.assertTrue(self.item.is_abnormal)
        self.assertEqual(self.item.result_notes, "Slightly elevated WBC")

    def test_lab_test_on_delete_set_null(self):
        """Deleting lab_test should set item.lab_test to NULL."""
        lab_test = LabTest.objects.create(
            clinic=self.clinic,
            name="Temporary Test",
        )
        item = LabOrderItem.objects.create(
            lab_order=self.lab_order,
            lab_test=lab_test,
            test_name="Temporary Test",
        )
        lab_test.delete()
        item.refresh_from_db()
        self.assertIsNone(item.lab_test)


class LabTestSerializerTestCase(TestCase):
    """Tests for the LabTestSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.lab_test = LabTest.objects.create(
            clinic=self.clinic,
            name="Complete Blood Count",
            code="CBC",
            category="hematology",
            sample_type="blood",
            description="Measures blood cell counts",
            turnaround_time="24-48 hours",
            price=Decimal("500.00"),
            special_instructions="Fasting not required",
            is_active=True,
        )

    def test_serializer_contains_expected_fields(self):
        """Serializer should contain all expected fields."""
        serializer = LabTestSerializer(self.lab_test)
        data = serializer.data

        expected_fields = [
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
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_category_display(self):
        """category_display should return human-readable value."""
        serializer = LabTestSerializer(self.lab_test)
        self.assertEqual(serializer.data["category_display"], "Hematology")

    def test_serializer_sample_type_display(self):
        """sample_type_display should return human-readable value."""
        serializer = LabTestSerializer(self.lab_test)
        self.assertEqual(serializer.data["sample_type_display"], "Blood")

    def test_serializer_display_name(self):
        """display_name should be included."""
        serializer = LabTestSerializer(self.lab_test)
        self.assertEqual(serializer.data["display_name"], "Complete Blood Count (CBC)")


class LabOrderSerializerTestCase(TestCase):
    """Tests for the LabOrderSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-15",
            gender="Male",
            phone="09171234567",
        )
        self.user = CustomUser.objects.create_user(
            username="doctor",
            email="doctor@example.com",
            password="testpass123",
            first_name="Dr. Jane",
            last_name="Smith",
            clinic=self.clinic,
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            created_by=self.user,
            consultation_id="CONS-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
        )
        self.lab_order = LabOrder.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            ordered_by=self.user,
            order_id="LAB-2026-0001",
            order_date=date.today(),
            priority="urgent",
            clinical_indication="Suspected infection",
            notes="Collect fasting sample",
        )
        LabOrderItem.objects.create(
            lab_order=self.lab_order,
            test_name="CBC",
            test_code="CBC",
            category="hematology",
            sample_type="blood",
        )

    def test_serializer_contains_expected_fields(self):
        """Serializer should contain all expected fields."""
        serializer = LabOrderSerializer(self.lab_order)
        data = serializer.data

        expected_fields = [
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
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_nested_items(self):
        """Serializer should include nested items."""
        serializer = LabOrderSerializer(self.lab_order)
        data = serializer.data

        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["test_name"], "CBC")

    def test_serializer_patient_name(self):
        """patient_name should be included."""
        serializer = LabOrderSerializer(self.lab_order)
        self.assertEqual(serializer.data["patient_name"], "John Doe")

    def test_serializer_doctor_name(self):
        """doctor_name should be included."""
        serializer = LabOrderSerializer(self.lab_order)
        self.assertEqual(serializer.data["doctor_name"], "Dr. Jane Smith")

    def test_serializer_status_display(self):
        """status_display should return human-readable status."""
        serializer = LabOrderSerializer(self.lab_order)
        self.assertEqual(serializer.data["status_display"], "Ordered")

    def test_serializer_priority_display(self):
        """priority_display should return human-readable priority."""
        serializer = LabOrderSerializer(self.lab_order)
        self.assertEqual(serializer.data["priority_display"], "Urgent")

    def test_serializer_test_count(self):
        """test_count should be included."""
        serializer = LabOrderSerializer(self.lab_order)
        self.assertEqual(serializer.data["test_count"], 1)


class LabOrderCreateUpdateSerializerTestCase(TestCase):
    """Tests for the LabOrderCreateUpdateSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-15",
            gender="Male",
            phone="09171234567",
        )
        self.user = CustomUser.objects.create_user(
            username="doctor",
            email="doctor@example.com",
            password="testpass123",
            clinic=self.clinic,
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            created_by=self.user,
            consultation_id="CONS-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
        )
        self.lab_test = LabTest.objects.create(
            clinic=self.clinic,
            name="Complete Blood Count",
            code="CBC",
            category="hematology",
            sample_type="blood",
        )
        self.valid_data = {
            "consultation": self.consultation.id,
            "order_date": date.today().isoformat(),
            "priority": "routine",
            "clinical_indication": "Annual checkup",
            "items": [
                {
                    "test_name": "Complete Blood Count",
                    "test_code": "CBC",
                    "category": "hematology",
                    "sample_type": "blood",
                }
            ],
        }

    def get_mock_request(self):
        """Create a mock request with user context."""
        request = self.factory.post("/")
        request.user = self.user
        drf_request = Request(request)
        drf_request.user = self.user
        return drf_request

    def test_create_lab_order_with_items(self):
        """Should create lab order with nested items."""
        serializer = LabOrderCreateUpdateSerializer(
            data=self.valid_data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        lab_order = serializer.save()

        self.assertEqual(lab_order.clinic, self.clinic)
        self.assertEqual(lab_order.patient, self.patient)
        self.assertEqual(lab_order.ordered_by, self.user)
        self.assertTrue(lab_order.order_id.startswith("LAB-"))
        self.assertEqual(lab_order.items.count(), 1)

    def test_create_lab_order_generates_id(self):
        """Should generate unique order ID."""
        serializer = LabOrderCreateUpdateSerializer(
            data=self.valid_data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        lab_order = serializer.save()

        self.assertRegex(lab_order.order_id, r"^LAB-\d{4}-\d{4}$")

    def test_create_lab_order_with_lab_test_id(self):
        """Should link item to lab_test when lab_test_id is provided."""
        data = self.valid_data.copy()
        data["items"] = [
            {
                "lab_test_id": self.lab_test.id,
                "test_name": "Complete Blood Count",
                "test_code": "CBC",
                "category": "hematology",
                "sample_type": "blood",
            }
        ]
        serializer = LabOrderCreateUpdateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        lab_order = serializer.save()

        item = lab_order.items.first()
        self.assertEqual(item.lab_test, self.lab_test)
        self.assertEqual(item.test_name, "Complete Blood Count")
        self.assertEqual(item.test_code, "CBC")
        self.assertEqual(item.category, "hematology")

    def test_update_lab_order(self):
        """Should update lab order fields."""
        lab_order = LabOrder.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            order_id="LAB-2026-0001",
            order_date=date.today(),
        )
        LabOrderItem.objects.create(
            lab_order=lab_order,
            test_name="Old Test",
        )

        update_data = {
            "consultation": self.consultation.id,
            "order_date": date.today().isoformat(),
            "priority": "stat",
            "status": "collected",
            "items": [
                {
                    "test_name": "New Test",
                    "test_code": "NT",
                }
            ],
        }
        serializer = LabOrderCreateUpdateSerializer(
            lab_order, data=update_data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.priority, "stat")
        self.assertEqual(updated.status, "collected")
        self.assertEqual(updated.items.count(), 1)
        self.assertEqual(updated.items.first().test_name, "New Test")

    def test_missing_required_fields(self):
        """Should fail without required fields."""
        data = {"notes": "Some notes"}
        serializer = LabOrderCreateUpdateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("consultation", serializer.errors)
        self.assertIn("order_date", serializer.errors)
        self.assertIn("items", serializer.errors)
