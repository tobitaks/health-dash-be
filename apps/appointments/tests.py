"""
Unit tests for the appointments app.
"""

from datetime import date, time, timedelta
from decimal import Decimal

from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from apps.appointments.models import Appointment
from apps.appointments.serializers import (
    AppointmentCreateUpdateSerializer,
    AppointmentSerializer,
)
from apps.clinic.models import Clinic, Service
from apps.patients.models import Patient
from apps.users.models import CustomUser


class AppointmentModelTestCase(TestCase):
    """Tests for the Appointment model."""

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
        self.service = Service.objects.create(
            clinic=self.clinic,
            name="General Consultation",
            code="GC001",
            price=Decimal("500.00"),
            duration_minutes=30,
        )
        self.user = CustomUser.objects.create_user(
            username="doctor",
            email="doctor@example.com",
            password="testpass123",
            clinic=self.clinic,
        )
        self.appointment = Appointment.objects.create(
            clinic=self.clinic,
            appointment_id="APT-2026-0001",
            patient=self.patient,
            service=self.service,
            assigned_to=self.user,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            duration_minutes=30,
        )

    def test_appointment_creation(self):
        """Appointment should be created with required fields."""
        self.assertEqual(self.appointment.appointment_id, "APT-2026-0001")
        self.assertEqual(self.appointment.patient, self.patient)
        self.assertEqual(self.appointment.service, self.service)
        self.assertEqual(self.appointment.status, "scheduled")

    def test_appointment_str(self):
        """Appointment __str__ should return ID, patient name, and date."""
        expected = f"APT-2026-0001 - John Doe ({self.appointment.date})"
        self.assertEqual(str(self.appointment), expected)

    def test_appointment_default_status(self):
        """Appointment status should default to 'scheduled'."""
        appointment = Appointment.objects.create(
            clinic=self.clinic,
            appointment_id="APT-2026-0002",
            patient=self.patient,
            service=self.service,
            date=date.today() + timedelta(days=2),
            time=time(14, 0),
        )
        self.assertEqual(appointment.status, "scheduled")

    def test_appointment_default_duration(self):
        """Appointment duration should default to 30 minutes."""
        appointment = Appointment.objects.create(
            clinic=self.clinic,
            appointment_id="APT-2026-0003",
            patient=self.patient,
            service=self.service,
            date=date.today() + timedelta(days=3),
            time=time(11, 0),
        )
        self.assertEqual(appointment.duration_minutes, 30)

    def test_appointment_unique_together_constraint(self):
        """Same appointment_id in same clinic should raise IntegrityError."""
        with self.assertRaises(IntegrityError):
            Appointment.objects.create(
                clinic=self.clinic,
                appointment_id="APT-2026-0001",  # Duplicate
                patient=self.patient,
                service=self.service,
                date=date.today() + timedelta(days=4),
                time=time(15, 0),
            )

    def test_appointment_same_id_different_clinic(self):
        """Same appointment_id in different clinic should be allowed."""
        clinic2 = Clinic.objects.create(name="Second Clinic")
        patient2 = Patient.objects.create(
            clinic=clinic2,
            patient_id="PT-2026-0001",
            first_name="Jane",
            last_name="Smith",
            date_of_birth="1985-05-20",
            gender="Female",
            phone="09181234567",
        )
        service2 = Service.objects.create(
            clinic=clinic2,
            name="Checkup",
            code="CHK001",
            price=Decimal("300.00"),
        )
        appointment2 = Appointment.objects.create(
            clinic=clinic2,
            appointment_id="APT-2026-0001",  # Same ID, different clinic
            patient=patient2,
            service=service2,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
        )
        self.assertEqual(appointment2.appointment_id, "APT-2026-0001")
        self.assertNotEqual(appointment2.clinic, self.appointment.clinic)

    def test_appointment_status_choices(self):
        """All valid status choices should be accepted."""
        valid_statuses = [
            "scheduled",
            "confirmed",
            "in-progress",
            "completed",
            "cancelled",
            "no-show",
        ]
        for i, status_choice in enumerate(valid_statuses):
            appointment = Appointment.objects.create(
                clinic=self.clinic,
                appointment_id=f"APT-2026-{100 + i:04d}",
                patient=self.patient,
                service=self.service,
                date=date.today() + timedelta(days=10 + i),
                time=time(9, 0),
                status=status_choice,
            )
            self.assertEqual(appointment.status, status_choice)

    def test_appointment_notes_optional(self):
        """Notes field should be optional and default to empty string."""
        self.assertEqual(self.appointment.notes, "")

    def test_appointment_with_notes(self):
        """Appointment should store notes correctly."""
        self.appointment.notes = "Patient requested early morning slot"
        self.appointment.save()
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.notes, "Patient requested early morning slot")

    def test_appointment_assigned_to_optional(self):
        """assigned_to field should be optional."""
        appointment = Appointment.objects.create(
            clinic=self.clinic,
            appointment_id="APT-2026-0050",
            patient=self.patient,
            service=self.service,
            date=date.today() + timedelta(days=5),
            time=time(16, 0),
            assigned_to=None,
        )
        self.assertIsNone(appointment.assigned_to)

    def test_appointment_service_on_delete_set_null(self):
        """Deleting service should set appointment.service to NULL."""
        service = Service.objects.create(
            clinic=self.clinic,
            name="Temporary Service",
            code="TEMP001",
            price=Decimal("100.00"),
        )
        appointment = Appointment.objects.create(
            clinic=self.clinic,
            appointment_id="APT-2026-0060",
            patient=self.patient,
            service=service,
            date=date.today() + timedelta(days=6),
            time=time(17, 0),
        )
        service.delete()
        appointment.refresh_from_db()
        self.assertIsNone(appointment.service)


class AppointmentSerializerTestCase(TestCase):
    """Tests for the AppointmentSerializer (read-only)."""

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
        )
        self.service = Service.objects.create(
            clinic=self.clinic,
            name="General Consultation",
            code="GC001",
            price=Decimal("500.00"),
        )
        self.user = CustomUser.objects.create_user(
            username="drdoe",
            email="dr.doe@example.com",
            password="testpass123",
            first_name="Dr. Jane",
            last_name="Doe",
            clinic=self.clinic,
        )
        self.appointment = Appointment.objects.create(
            clinic=self.clinic,
            appointment_id="APT-2026-0001",
            patient=self.patient,
            service=self.service,
            assigned_to=self.user,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            duration_minutes=45,
            status="confirmed",
            notes="Follow-up appointment",
        )

    def test_serializer_contains_expected_fields(self):
        """Serializer should contain all expected fields."""
        serializer = AppointmentSerializer(self.appointment)
        data = serializer.data

        expected_fields = [
            "id",
            "appointment_id",
            "patient",
            "patient_name",
            "service",
            "service_name",
            "assigned_to",
            "assigned_to_name",
            "date",
            "time",
            "duration_minutes",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serializer_patient_name(self):
        """patient_name should return patient's full name."""
        serializer = AppointmentSerializer(self.appointment)
        self.assertEqual(serializer.data["patient_name"], "John Michael Doe")

    def test_serializer_service_name(self):
        """service_name should return service's name."""
        serializer = AppointmentSerializer(self.appointment)
        self.assertEqual(serializer.data["service_name"], "General Consultation")

    def test_serializer_assigned_to_name(self):
        """assigned_to_name should return staff member's name."""
        serializer = AppointmentSerializer(self.appointment)
        self.assertEqual(serializer.data["assigned_to_name"], "Dr. Jane Doe")

    def test_serializer_assigned_to_name_none(self):
        """assigned_to_name should be None when no staff assigned."""
        self.appointment.assigned_to = None
        self.appointment.save()
        serializer = AppointmentSerializer(self.appointment)
        self.assertIsNone(serializer.data["assigned_to_name"])

    def test_serializer_service_name_none(self):
        """service_name should be None when service is deleted."""
        self.appointment.service = None
        self.appointment.save()
        serializer = AppointmentSerializer(self.appointment)
        self.assertIsNone(serializer.data["service_name"])

    def test_serializer_read_only_fields(self):
        """Read-only fields should be defined correctly."""
        self.assertIn("id", AppointmentSerializer.Meta.read_only_fields)
        self.assertIn("appointment_id", AppointmentSerializer.Meta.read_only_fields)
        self.assertIn("created_at", AppointmentSerializer.Meta.read_only_fields)
        self.assertIn("updated_at", AppointmentSerializer.Meta.read_only_fields)


class AppointmentCreateUpdateSerializerTestCase(TestCase):
    """Tests for the AppointmentCreateUpdateSerializer."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.clinic2 = Clinic.objects.create(name="Other Clinic")
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-15",
            gender="Male",
            phone="09171234567",
        )
        self.patient_other_clinic = Patient.objects.create(
            clinic=self.clinic2,
            patient_id="PT-2026-0001",
            first_name="Jane",
            last_name="Smith",
            date_of_birth="1985-05-20",
            gender="Female",
            phone="09181234567",
        )
        self.service = Service.objects.create(
            clinic=self.clinic,
            name="General Consultation",
            code="GC001",
            price=Decimal("500.00"),
        )
        self.service_other_clinic = Service.objects.create(
            clinic=self.clinic2,
            name="Checkup",
            code="CHK001",
            price=Decimal("300.00"),
        )
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            clinic=self.clinic,
        )
        self.valid_data = {
            "patient": self.patient.id,
            "service": self.service.id,
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "time": "10:00:00",
            "duration_minutes": 30,
            "status": "scheduled",
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
        serializer = AppointmentCreateUpdateSerializer(
            data=self.valid_data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_required_fields(self):
        """Serializer should fail without required fields."""
        data = {"notes": "Some notes"}
        serializer = AppointmentCreateUpdateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("patient", serializer.errors)
        self.assertIn("date", serializer.errors)
        self.assertIn("time", serializer.errors)

    def test_patient_from_different_clinic_invalid(self):
        """Patient from different clinic should fail validation."""
        data = self.valid_data.copy()
        data["patient"] = self.patient_other_clinic.id
        serializer = AppointmentCreateUpdateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("patient", serializer.errors)
        self.assertIn("clinic", str(serializer.errors["patient"][0]).lower())

    def test_service_from_different_clinic_invalid(self):
        """Service from different clinic should fail validation."""
        data = self.valid_data.copy()
        data["service"] = self.service_other_clinic.id
        serializer = AppointmentCreateUpdateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("service", serializer.errors)
        self.assertIn("clinic", str(serializer.errors["service"][0]).lower())

    def test_service_null_allowed(self):
        """Service can be null."""
        data = self.valid_data.copy()
        data["service"] = None
        serializer = AppointmentCreateUpdateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_date_in_past_invalid_for_new_appointment(self):
        """Date in the past should be invalid for new appointments."""
        past_date = date.today() - timedelta(days=1)
        data = self.valid_data.copy()
        data["date"] = past_date.isoformat()
        serializer = AppointmentCreateUpdateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("date", serializer.errors)
        self.assertIn("past", str(serializer.errors["date"][0]).lower())

    def test_date_today_valid(self):
        """Date today should be valid for new appointments."""
        data = self.valid_data.copy()
        data["date"] = date.today().isoformat()
        serializer = AppointmentCreateUpdateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_date_in_past_valid_for_existing_appointment(self):
        """Date in the past should be valid when updating existing appointment."""
        # Create an existing appointment
        appointment = Appointment.objects.create(
            clinic=self.clinic,
            appointment_id="APT-2026-0001",
            patient=self.patient,
            service=self.service,
            date=date.today() - timedelta(days=5),  # Past date
            time=time(10, 0),
        )
        # Update the appointment with a past date
        past_date = date.today() - timedelta(days=10)
        data = {"date": past_date.isoformat()}
        serializer = AppointmentCreateUpdateSerializer(
            appointment,
            data=data,
            partial=True,
            context={"request": self.get_mock_request()},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_status_choice(self):
        """Invalid status choice should fail validation."""
        data = self.valid_data.copy()
        data["status"] = "invalid-status"
        serializer = AppointmentCreateUpdateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)

    def test_valid_status_choices(self):
        """All valid status choices should pass validation."""
        valid_statuses = [
            "scheduled",
            "confirmed",
            "in-progress",
            "completed",
            "cancelled",
            "no-show",
        ]
        for status_choice in valid_statuses:
            data = self.valid_data.copy()
            data["status"] = status_choice
            serializer = AppointmentCreateUpdateSerializer(
                data=data, context={"request": self.get_mock_request()}
            )
            self.assertTrue(
                serializer.is_valid(), f"Status '{status_choice}' should be valid"
            )

    def test_partial_update(self):
        """Serializer should support partial updates."""
        appointment = Appointment.objects.create(
            clinic=self.clinic,
            appointment_id="APT-2026-0001",
            patient=self.patient,
            service=self.service,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            status="scheduled",
        )
        update_data = {"status": "confirmed", "notes": "Confirmed by phone"}
        serializer = AppointmentCreateUpdateSerializer(
            appointment,
            data=update_data,
            partial=True,
            context={"request": self.get_mock_request()},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.status, "confirmed")
        self.assertEqual(updated.notes, "Confirmed by phone")

    def test_duration_minutes_positive(self):
        """Duration minutes should be a positive integer."""
        data = self.valid_data.copy()
        data["duration_minutes"] = 60
        serializer = AppointmentCreateUpdateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["duration_minutes"], 60)


class GenerateAppointmentIdTestCase(TestCase):
    """Tests for the generate_appointment_id helper function."""

    def setUp(self):
        """Set up test fixtures."""
        from apps.api.appointment_views import generate_appointment_id

        self.generate_appointment_id = generate_appointment_id
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
        self.service = Service.objects.create(
            clinic=self.clinic,
            name="Consultation",
            code="CON001",
            price=Decimal("500.00"),
        )

    def test_first_appointment_id(self):
        """First appointment should get ID ending in 0001."""
        appointment_id = self.generate_appointment_id(self.clinic)
        self.assertTrue(appointment_id.endswith("-0001"))
        self.assertTrue(appointment_id.startswith("APT-"))

    def test_sequential_appointment_ids(self):
        """Appointment IDs should be sequential."""
        # Create first appointment
        Appointment.objects.create(
            clinic=self.clinic,
            appointment_id=self.generate_appointment_id(self.clinic),
            patient=self.patient,
            service=self.service,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
        )

        # Generate second ID
        second_id = self.generate_appointment_id(self.clinic)
        self.assertTrue(second_id.endswith("-0002"))

    def test_appointment_id_format(self):
        """Appointment ID should follow APT-YYYY-#### format."""
        import re
        from datetime import datetime

        appointment_id = self.generate_appointment_id(self.clinic)
        year = datetime.now().year
        pattern = rf"^APT-{year}-\d{{4}}$"
        self.assertIsNotNone(re.match(pattern, appointment_id))

    def test_appointment_id_per_clinic(self):
        """Each clinic should have its own sequence."""
        clinic2 = Clinic.objects.create(name="Second Clinic")
        patient2 = Patient.objects.create(
            clinic=clinic2,
            patient_id="PT-2026-0001",
            first_name="Jane",
            last_name="Smith",
            date_of_birth="1985-05-20",
            gender="Female",
            phone="09181234567",
        )
        service2 = Service.objects.create(
            clinic=clinic2,
            name="Checkup",
            code="CHK001",
            price=Decimal("300.00"),
        )

        # Create appointment in first clinic
        Appointment.objects.create(
            clinic=self.clinic,
            appointment_id=self.generate_appointment_id(self.clinic),
            patient=self.patient,
            service=self.service,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
        )

        # First appointment in second clinic should also be 0001
        appointment_id_clinic2 = self.generate_appointment_id(clinic2)
        self.assertTrue(appointment_id_clinic2.endswith("-0001"))

    def test_appointment_id_continues_sequence(self):
        """Sequence should continue from last appointment."""
        # Create 5 appointments
        for i in range(1, 6):
            Appointment.objects.create(
                clinic=self.clinic,
                appointment_id=f"APT-2026-{i:04d}",
                patient=self.patient,
                service=self.service,
                date=date.today() + timedelta(days=i),
                time=time(9, 0),
            )

        # Next ID should be 0006
        next_id = self.generate_appointment_id(self.clinic)
        self.assertTrue(next_id.endswith("-0006"))
