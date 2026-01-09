"""
Unit tests for the patients app.
"""

from datetime import date, timedelta

from django.db import IntegrityError
from django.test import TestCase

from apps.clinic.models import Clinic
from apps.patients.models import Patient
from apps.patients.serializers import PatientCreateUpdateSerializer, PatientSerializer


class PatientModelTestCase(TestCase):
    """Tests for the Patient model."""

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

    def test_patient_creation(self):
        """Patient should be created with required fields."""
        self.assertEqual(self.patient.first_name, "John")
        self.assertEqual(self.patient.last_name, "Doe")
        self.assertEqual(self.patient.patient_id, "PT-2026-0001")
        self.assertEqual(self.patient.gender, "Male")
        self.assertEqual(self.patient.status, "active")

    def test_patient_str(self):
        """Patient __str__ should return patient_id and name."""
        self.assertEqual(str(self.patient), "PT-2026-0001 - John Doe")

    def test_full_name_without_middle_name(self):
        """full_name should return first and last name when no middle name."""
        self.assertEqual(self.patient.full_name, "John Doe")

    def test_full_name_with_middle_name(self):
        """full_name should include middle name when present."""
        self.patient.middle_name = "Michael"
        self.patient.save()
        self.assertEqual(self.patient.full_name, "John Michael Doe")

    def test_patient_default_status(self):
        """Patient status should default to 'active'."""
        patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0002",
            first_name="Jane",
            last_name="Smith",
            date_of_birth="1985-05-20",
            gender="Female",
            phone="09181234567",
        )
        self.assertEqual(patient.status, "active")

    def test_patient_unique_together_constraint(self):
        """Same patient_id in same clinic should raise IntegrityError."""
        with self.assertRaises(IntegrityError):
            Patient.objects.create(
                clinic=self.clinic,
                patient_id="PT-2026-0001",  # Duplicate
                first_name="Another",
                last_name="Patient",
                date_of_birth="1995-03-10",
                gender="Male",
                phone="09191234567",
            )

    def test_patient_same_id_different_clinic(self):
        """Same patient_id in different clinic should be allowed."""
        clinic2 = Clinic.objects.create(name="Another Clinic")
        patient2 = Patient.objects.create(
            clinic=clinic2,
            patient_id="PT-2026-0001",  # Same ID, different clinic
            first_name="Different",
            last_name="Patient",
            date_of_birth="1992-07-25",
            gender="Female",
            phone="09201234567",
        )
        self.assertEqual(patient2.patient_id, "PT-2026-0001")
        self.assertNotEqual(patient2.clinic, self.patient.clinic)

    def test_patient_optional_fields_default_empty(self):
        """Optional fields should have empty defaults."""
        self.assertEqual(self.patient.middle_name, "")
        self.assertEqual(self.patient.email, "")
        self.assertEqual(self.patient.address_street, "")
        self.assertEqual(self.patient.blood_type, "")
        self.assertEqual(self.patient.allergies, [])
        self.assertEqual(self.patient.medical_conditions, [])
        self.assertEqual(self.patient.current_medications, "")

    def test_patient_json_fields(self):
        """JSONField allergies and medical_conditions should store lists."""
        self.patient.allergies = ["Penicillin", "Peanuts"]
        self.patient.medical_conditions = ["Diabetes", "Hypertension"]
        self.patient.save()

        self.patient.refresh_from_db()
        self.assertEqual(self.patient.allergies, ["Penicillin", "Peanuts"])
        self.assertEqual(self.patient.medical_conditions, ["Diabetes", "Hypertension"])


class PatientSerializerTestCase(TestCase):
    """Tests for the PatientSerializer (read-only)."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="John",
            middle_name="Michael",
            last_name="Doe",
            date_of_birth="1990-01-15",
            gender="Male",
            phone="09171234567",
            email="john.doe@example.com",
            blood_type="O+",
            allergies=["Penicillin"],
        )

    def test_serializer_contains_expected_fields(self):
        """Serializer should contain all expected fields."""
        serializer = PatientSerializer(self.patient)
        data = serializer.data

        expected_fields = [
            "id",
            "patient_id",
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "gender",
            "civil_status",
            "phone",
            "status",
            "email",
            "address_street",
            "address_city",
            "address_province",
            "address_zip",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
            "blood_type",
            "allergies",
            "medical_conditions",
            "current_medications",
            "created_at",
            "updated_at",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_read_only_fields(self):
        """Read-only fields should not be writable."""
        serializer = PatientSerializer(self.patient)
        self.assertIn("id", serializer.Meta.read_only_fields)
        self.assertIn("patient_id", serializer.Meta.read_only_fields)
        self.assertIn("created_at", serializer.Meta.read_only_fields)
        self.assertIn("updated_at", serializer.Meta.read_only_fields)

    def test_serializer_data_values(self):
        """Serializer should return correct data values."""
        serializer = PatientSerializer(self.patient)
        data = serializer.data

        self.assertEqual(data["first_name"], "John")
        self.assertEqual(data["middle_name"], "Michael")
        self.assertEqual(data["last_name"], "Doe")
        self.assertEqual(data["gender"], "Male")
        self.assertEqual(data["blood_type"], "O+")
        self.assertEqual(data["allergies"], ["Penicillin"])


class PatientCreateUpdateSerializerTestCase(TestCase):
    """Tests for the PatientCreateUpdateSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.valid_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "1985-05-20",
            "gender": "Female",
            "phone": "09181234567",
        }

    def test_valid_data_is_valid(self):
        """Serializer should validate with valid data."""
        serializer = PatientCreateUpdateSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_required_fields(self):
        """Serializer should fail without required fields."""
        data = {"first_name": "Jane"}
        serializer = PatientCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("last_name", serializer.errors)
        self.assertIn("date_of_birth", serializer.errors)
        self.assertIn("gender", serializer.errors)
        self.assertIn("phone", serializer.errors)

    def test_date_of_birth_in_future_invalid(self):
        """Date of birth in the future should be invalid."""
        future_date = date.today() + timedelta(days=1)
        data = self.valid_data.copy()
        data["date_of_birth"] = future_date.isoformat()
        serializer = PatientCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("date_of_birth", serializer.errors)
        self.assertIn("future", str(serializer.errors["date_of_birth"][0]).lower())

    def test_date_of_birth_today_valid(self):
        """Date of birth today should be valid (for newborns)."""
        data = self.valid_data.copy()
        data["date_of_birth"] = date.today().isoformat()
        serializer = PatientCreateUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_date_of_birth_past_valid(self):
        """Date of birth in the past should be valid."""
        past_date = date.today() - timedelta(days=365 * 30)  # 30 years ago
        data = self.valid_data.copy()
        data["date_of_birth"] = past_date.isoformat()
        serializer = PatientCreateUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_gender_choice(self):
        """Invalid gender choice should fail validation."""
        data = self.valid_data.copy()
        data["gender"] = "InvalidGender"
        serializer = PatientCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("gender", serializer.errors)

    def test_valid_gender_choices(self):
        """All valid gender choices should pass validation."""
        for gender in ["Male", "Female", "Other"]:
            data = self.valid_data.copy()
            data["gender"] = gender
            serializer = PatientCreateUpdateSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Gender '{gender}' should be valid")

    def test_optional_fields_can_be_empty(self):
        """Optional fields can be omitted or empty."""
        serializer = PatientCreateUpdateSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        # Optional fields should not be in errors

    def test_allergies_as_list(self):
        """Allergies field should accept a list."""
        data = self.valid_data.copy()
        data["allergies"] = ["Penicillin", "Aspirin"]
        serializer = PatientCreateUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["allergies"], ["Penicillin", "Aspirin"])

    def test_medical_conditions_as_list(self):
        """Medical conditions field should accept a list."""
        data = self.valid_data.copy()
        data["medical_conditions"] = ["Diabetes", "Hypertension"]
        serializer = PatientCreateUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["medical_conditions"], ["Diabetes", "Hypertension"])

    def test_update_patient(self):
        """Serializer should update existing patient."""
        patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-15",
            gender="Male",
            phone="09171234567",
        )
        update_data = {"first_name": "Johnny", "phone": "09999999999"}
        serializer = PatientCreateUpdateSerializer(patient, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_patient = serializer.save()
        self.assertEqual(updated_patient.first_name, "Johnny")
        self.assertEqual(updated_patient.phone, "09999999999")
        self.assertEqual(updated_patient.last_name, "Doe")  # Unchanged

    def test_blood_type_choices(self):
        """Valid blood type choices should pass validation."""
        valid_blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"]
        for blood_type in valid_blood_types:
            data = self.valid_data.copy()
            data["blood_type"] = blood_type
            serializer = PatientCreateUpdateSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Blood type '{blood_type}' should be valid")

    def test_invalid_blood_type(self):
        """Invalid blood type should fail validation."""
        data = self.valid_data.copy()
        data["blood_type"] = "X+"
        serializer = PatientCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("blood_type", serializer.errors)


class GeneratePatientIdTestCase(TestCase):
    """Tests for the generate_patient_id helper function."""

    def setUp(self):
        """Set up test fixtures."""
        from apps.api.patient_views import generate_patient_id

        self.generate_patient_id = generate_patient_id
        self.clinic = Clinic.objects.create(name="Test Clinic")

    def test_first_patient_id(self):
        """First patient should get ID ending in 0001."""
        patient_id = self.generate_patient_id(self.clinic)
        self.assertTrue(patient_id.endswith("-0001"))
        self.assertTrue(patient_id.startswith("PT-"))

    def test_sequential_patient_ids(self):
        """Patient IDs should be sequential."""
        # Create first patient
        Patient.objects.create(
            clinic=self.clinic,
            patient_id=self.generate_patient_id(self.clinic),
            first_name="First",
            last_name="Patient",
            date_of_birth="1990-01-01",
            gender="Male",
            phone="09171111111",
        )

        # Generate second ID
        second_id = self.generate_patient_id(self.clinic)
        self.assertTrue(second_id.endswith("-0002"))

    def test_patient_id_format(self):
        """Patient ID should follow PT-YYYY-#### format."""
        import re
        from datetime import datetime

        patient_id = self.generate_patient_id(self.clinic)
        year = datetime.now().year
        pattern = rf"^PT-{year}-\d{{4}}$"
        self.assertIsNotNone(re.match(pattern, patient_id))

    def test_patient_id_per_clinic(self):
        """Each clinic should have its own sequence."""
        clinic2 = Clinic.objects.create(name="Second Clinic")

        # Create patient in first clinic
        Patient.objects.create(
            clinic=self.clinic,
            patient_id=self.generate_patient_id(self.clinic),
            first_name="Clinic1",
            last_name="Patient",
            date_of_birth="1990-01-01",
            gender="Male",
            phone="09171111111",
        )

        # First patient in second clinic should also be 0001
        patient_id_clinic2 = self.generate_patient_id(clinic2)
        self.assertTrue(patient_id_clinic2.endswith("-0001"))

    def test_patient_id_continues_sequence(self):
        """Sequence should continue from last patient."""
        # Create 5 patients
        for i in range(1, 6):
            Patient.objects.create(
                clinic=self.clinic,
                patient_id=f"PT-2026-{i:04d}",
                first_name=f"Patient{i}",
                last_name="Test",
                date_of_birth="1990-01-01",
                gender="Male",
                phone=f"0917{i:07d}",
            )

        # Next ID should be 0006
        next_id = self.generate_patient_id(self.clinic)
        self.assertTrue(next_id.endswith("-0006"))
