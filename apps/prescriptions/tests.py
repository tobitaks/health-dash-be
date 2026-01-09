"""
Unit tests for the prescriptions app.
"""

from datetime import date

from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from apps.clinic.models import Clinic
from apps.consultations.models import Consultation
from apps.medicines.models import Medicine
from apps.patients.models import Patient
from apps.prescriptions.models import Prescription, PrescriptionItem
from apps.prescriptions.serializers import (
    PrescriptionCreateUpdateSerializer,
    PrescriptionItemSerializer,
    PrescriptionSerializer,
)
from apps.users.models import CustomUser


class PrescriptionModelTestCase(TestCase):
    """Tests for the Prescription model."""

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
        self.prescription = Prescription.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            prescribed_by=self.user,
            prescription_id="RX-2026-0001",
            prescription_date=date.today(),
        )

    def test_prescription_creation(self):
        """Prescription should be created with required fields."""
        self.assertEqual(self.prescription.prescription_id, "RX-2026-0001")
        self.assertEqual(self.prescription.patient, self.patient)
        self.assertEqual(self.prescription.prescribed_by, self.user)
        self.assertEqual(self.prescription.status, "active")

    def test_prescription_str(self):
        """Prescription __str__ should return ID and patient."""
        expected = f"RX-2026-0001 - {self.patient}"
        self.assertEqual(str(self.prescription), expected)

    def test_prescription_default_status(self):
        """Prescription status should default to 'active'."""
        self.assertEqual(self.prescription.status, "active")

    def test_prescription_status_choices(self):
        """All valid status choices should be accepted."""
        # Create new consultations for each prescription
        for i, status in enumerate(["active", "completed", "cancelled"]):
            consultation = Consultation.objects.create(
                clinic=self.clinic,
                patient=self.patient,
                created_by=self.user,
                consultation_id=f"CONS-2026-{100 + i:04d}",
                consultation_date=date.today(),
                consultation_time="10:00:00",
            )
            prescription = Prescription.objects.create(
                clinic=self.clinic,
                consultation=consultation,
                patient=self.patient,
                prescription_id=f"RX-2026-{100 + i:04d}",
                prescription_date=date.today(),
                status=status,
            )
            self.assertEqual(prescription.status, status)

    def test_prescription_unique_together_constraint(self):
        """Same prescription_id in same clinic should raise IntegrityError."""
        consultation2 = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            created_by=self.user,
            consultation_id="CONS-2026-0002",
            consultation_date=date.today(),
            consultation_time="11:00:00",
        )
        with self.assertRaises(IntegrityError):
            Prescription.objects.create(
                clinic=self.clinic,
                consultation=consultation2,
                patient=self.patient,
                prescription_id="RX-2026-0001",  # Duplicate
                prescription_date=date.today(),
            )

    def test_prescription_same_id_different_clinic(self):
        """Same prescription_id in different clinic should be allowed."""
        clinic2 = Clinic.objects.create(name="Another Clinic")
        patient2 = Patient.objects.create(
            clinic=clinic2,
            patient_id="PT-2026-0001",
            first_name="Jane",
            last_name="Smith",
            date_of_birth="1985-05-20",
            gender="Female",
            phone="09181234567",
        )
        user2 = CustomUser.objects.create_user(
            username="doctor2",
            email="doctor2@example.com",
            password="testpass123",
            clinic=clinic2,
        )
        consultation2 = Consultation.objects.create(
            clinic=clinic2,
            patient=patient2,
            created_by=user2,
            consultation_id="CONS-2026-0001",
            consultation_date=date.today(),
            consultation_time="10:00:00",
        )
        prescription2 = Prescription.objects.create(
            clinic=clinic2,
            consultation=consultation2,
            patient=patient2,
            prescription_id="RX-2026-0001",  # Same ID, different clinic
            prescription_date=date.today(),
        )
        self.assertEqual(prescription2.prescription_id, "RX-2026-0001")
        self.assertNotEqual(prescription2.clinic, self.clinic)

    def test_patient_name_property(self):
        """patient_name should return patient's full name."""
        self.assertEqual(self.prescription.patient_name, "John Doe")

    def test_doctor_name_property(self):
        """doctor_name should return prescriber's name."""
        self.assertEqual(self.prescription.doctor_name, "Dr. Jane Smith")

    def test_doctor_name_property_no_prescriber(self):
        """doctor_name should return empty string if no prescriber."""
        self.prescription.prescribed_by = None
        self.prescription.save()
        self.assertEqual(self.prescription.doctor_name, "")

    def test_medicine_count_property(self):
        """medicine_count should return number of items."""
        self.assertEqual(self.prescription.medicine_count, 0)
        PrescriptionItem.objects.create(
            prescription=self.prescription,
            medicine_name="Paracetamol 500mg Tablet",
            sig="Take 1 tablet every 4-6 hours",
            quantity=20,
        )
        self.assertEqual(self.prescription.medicine_count, 1)

    def test_prescription_notes_optional(self):
        """Notes should be optional."""
        self.assertEqual(self.prescription.notes, "")


class PrescriptionItemModelTestCase(TestCase):
    """Tests for the PrescriptionItem model."""

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
        self.prescription = Prescription.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            prescription_id="RX-2026-0001",
            prescription_date=date.today(),
        )
        self.medicine = Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Paracetamol",
            brand_name="Biogesic",
            strength="500mg",
            form="tablet",
        )
        self.item = PrescriptionItem.objects.create(
            prescription=self.prescription,
            medicine=self.medicine,
            medicine_name="Paracetamol (Biogesic)",
            strength="500mg",
            form="Tablet",
            sig="Take 1 tablet every 4-6 hours as needed for pain",
            quantity=20,
        )

    def test_prescription_item_creation(self):
        """PrescriptionItem should be created with required fields."""
        self.assertEqual(self.item.medicine_name, "Paracetamol (Biogesic)")
        self.assertEqual(self.item.strength, "500mg")
        self.assertEqual(self.item.form, "Tablet")
        self.assertEqual(self.item.quantity, 20)

    def test_prescription_item_str(self):
        """PrescriptionItem __str__ should return medicine name and sig."""
        expected = "Paracetamol (Biogesic) - Take 1 tablet every 4-6 hours as needed for pain"
        self.assertEqual(str(self.item), expected)

    def test_display_name_property(self):
        """display_name should return formatted medicine name."""
        self.assertEqual(self.item.display_name, "Paracetamol (Biogesic) 500mg Tablet")

    def test_display_name_without_strength_form(self):
        """display_name should work without strength and form."""
        item = PrescriptionItem.objects.create(
            prescription=self.prescription,
            medicine_name="Vitamin C",
            sig="Take once daily",
            quantity=30,
        )
        self.assertEqual(item.display_name, "Vitamin C")

    def test_prescription_item_notes_optional(self):
        """Notes should be optional."""
        self.assertEqual(self.item.notes, "")

    def test_prescription_item_with_notes(self):
        """Notes should be stored correctly."""
        self.item.notes = "Take with food"
        self.item.save()
        self.item.refresh_from_db()
        self.assertEqual(self.item.notes, "Take with food")

    def test_prescription_item_medicine_optional(self):
        """Medicine FK should be optional."""
        item = PrescriptionItem.objects.create(
            prescription=self.prescription,
            medicine=None,
            medicine_name="Custom Medicine",
            sig="As directed",
            quantity=10,
        )
        self.assertIsNone(item.medicine)

    def test_medicine_on_delete_set_null(self):
        """Deleting medicine should set item.medicine to NULL."""
        medicine = Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Temporary",
            strength="100mg",
            form="tablet",
        )
        item = PrescriptionItem.objects.create(
            prescription=self.prescription,
            medicine=medicine,
            medicine_name="Temporary",
            sig="Take once",
            quantity=5,
        )
        medicine.delete()
        item.refresh_from_db()
        self.assertIsNone(item.medicine)


class PrescriptionSerializerTestCase(TestCase):
    """Tests for the PrescriptionSerializer."""

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
        self.prescription = Prescription.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            prescribed_by=self.user,
            prescription_id="RX-2026-0001",
            prescription_date=date.today(),
            notes="Take with food",
        )
        PrescriptionItem.objects.create(
            prescription=self.prescription,
            medicine_name="Paracetamol 500mg",
            sig="1 tablet every 4-6 hours",
            quantity=20,
        )

    def test_serializer_contains_expected_fields(self):
        """Serializer should contain all expected fields."""
        serializer = PrescriptionSerializer(self.prescription)
        data = serializer.data

        expected_fields = [
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
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_nested_items(self):
        """Serializer should include nested items."""
        serializer = PrescriptionSerializer(self.prescription)
        data = serializer.data

        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["medicine_name"], "Paracetamol 500mg")

    def test_serializer_patient_name(self):
        """patient_name should be included."""
        serializer = PrescriptionSerializer(self.prescription)
        self.assertEqual(serializer.data["patient_name"], "John Doe")

    def test_serializer_doctor_name(self):
        """doctor_name should be included."""
        serializer = PrescriptionSerializer(self.prescription)
        self.assertEqual(serializer.data["doctor_name"], "Dr. Jane Smith")

    def test_serializer_status_display(self):
        """status_display should return human-readable status."""
        serializer = PrescriptionSerializer(self.prescription)
        self.assertEqual(serializer.data["status_display"], "Active")

    def test_serializer_medicine_count(self):
        """medicine_count should be included."""
        serializer = PrescriptionSerializer(self.prescription)
        self.assertEqual(serializer.data["medicine_count"], 1)


class PrescriptionItemSerializerTestCase(TestCase):
    """Tests for the PrescriptionItemSerializer."""

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
        self.prescription = Prescription.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            prescription_id="RX-2026-0001",
            prescription_date=date.today(),
        )
        self.medicine = Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Paracetamol",
            strength="500mg",
            form="tablet",
        )
        self.item = PrescriptionItem.objects.create(
            prescription=self.prescription,
            medicine=self.medicine,
            medicine_name="Paracetamol",
            strength="500mg",
            form="Tablet",
            sig="Take 1 tablet every 4 hours",
            quantity=20,
            notes="For fever",
        )

    def test_serializer_contains_expected_fields(self):
        """Serializer should contain all expected fields."""
        serializer = PrescriptionItemSerializer(self.item)
        data = serializer.data

        expected_fields = [
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
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_medicine_id(self):
        """medicine_id should return linked medicine ID."""
        serializer = PrescriptionItemSerializer(self.item)
        self.assertEqual(serializer.data["medicine_id"], self.medicine.id)

    def test_serializer_medicine_id_none(self):
        """medicine_id should be None if no medicine linked."""
        item = PrescriptionItem.objects.create(
            prescription=self.prescription,
            medicine=None,
            medicine_name="Custom Drug",
            sig="As directed",
            quantity=10,
        )
        serializer = PrescriptionItemSerializer(item)
        self.assertIsNone(serializer.data["medicine_id"])

    def test_serializer_display_name(self):
        """display_name should be included."""
        serializer = PrescriptionItemSerializer(self.item)
        self.assertEqual(serializer.data["display_name"], "Paracetamol 500mg Tablet")


class PrescriptionCreateUpdateSerializerTestCase(TestCase):
    """Tests for the PrescriptionCreateUpdateSerializer."""

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
        self.medicine = Medicine.objects.create(
            clinic=self.clinic,
            generic_name="Paracetamol",
            strength="500mg",
            form="tablet",
        )
        self.valid_data = {
            "consultation": self.consultation.id,
            "prescription_date": date.today().isoformat(),
            "notes": "Take medications as prescribed",
            "items": [
                {
                    "medicine_name": "Paracetamol 500mg Tablet",
                    "strength": "500mg",
                    "form": "Tablet",
                    "sig": "1 tablet every 4-6 hours",
                    "quantity": 20,
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

    def test_create_prescription_with_items(self):
        """Should create prescription with nested items."""
        serializer = PrescriptionCreateUpdateSerializer(
            data=self.valid_data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        prescription = serializer.save()

        self.assertEqual(prescription.clinic, self.clinic)
        self.assertEqual(prescription.patient, self.patient)
        self.assertEqual(prescription.prescribed_by, self.user)
        self.assertTrue(prescription.prescription_id.startswith("RX-"))
        self.assertEqual(prescription.items.count(), 1)

    def test_create_prescription_generates_id(self):
        """Should generate unique prescription ID."""
        serializer = PrescriptionCreateUpdateSerializer(
            data=self.valid_data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        prescription = serializer.save()

        self.assertRegex(prescription.prescription_id, r"^RX-\d{4}-\d{4}$")

    def test_create_prescription_with_medicine_id(self):
        """Should link item to medicine when medicine_id provided."""
        data = self.valid_data.copy()
        data["items"] = [
            {
                "medicine_id": self.medicine.id,
                "medicine_name": "Paracetamol",
                "sig": "Take as directed",
                "quantity": 10,
            }
        ]
        serializer = PrescriptionCreateUpdateSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        prescription = serializer.save()

        self.assertEqual(prescription.items.first().medicine, self.medicine)

    def test_update_prescription(self):
        """Should update prescription fields."""
        prescription = Prescription.objects.create(
            clinic=self.clinic,
            consultation=self.consultation,
            patient=self.patient,
            prescription_id="RX-2026-0001",
            prescription_date=date.today(),
        )
        PrescriptionItem.objects.create(
            prescription=prescription,
            medicine_name="Old Medicine",
            sig="Old sig",
            quantity=5,
        )

        update_data = {
            "consultation": self.consultation.id,
            "prescription_date": date.today().isoformat(),
            "notes": "Updated notes",
            "status": "completed",
            "items": [
                {
                    "medicine_name": "New Medicine",
                    "sig": "New sig",
                    "quantity": 10,
                }
            ],
        }
        serializer = PrescriptionCreateUpdateSerializer(
            prescription, data=update_data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.notes, "Updated notes")
        self.assertEqual(updated.status, "completed")
        self.assertEqual(updated.items.count(), 1)
        self.assertEqual(updated.items.first().medicine_name, "New Medicine")

    def test_missing_required_fields(self):
        """Should fail without required fields."""
        data = {"notes": "Some notes"}
        serializer = PrescriptionCreateUpdateSerializer(data=data, context={"request": self.get_mock_request()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("consultation", serializer.errors)
        self.assertIn("prescription_date", serializer.errors)
        self.assertIn("items", serializer.errors)
