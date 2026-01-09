"""
Unit tests for consultation serializers.
"""

from django.test import RequestFactory, TestCase
from rest_framework.request import Request

from apps.clinic.models import Clinic
from apps.consultations.models import Consultation
from apps.consultations.serializers import (
    ConsultationBasicUpdateSerializer,
    ConsultationCreateSerializer,
    ConsultationFollowUpUpdateSerializer,
    ConsultationSOAPUpdateSerializer,
)
from apps.patients.models import Patient
from apps.users.models import CustomUser


class ConsultationSerializerTestCase(TestCase):
    """Base test case with common fixtures for consultation tests."""

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
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-15",
            gender="Male",
            phone="09171234567",
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            created_by=self.user,
            consultation_id="CONS-2026-0001",
            consultation_date="2026-01-09",
            consultation_time="10:00:00",
        )

    def get_mock_request(self):
        """Create a mock request with user context."""
        request = self.factory.get("/")
        request.user = self.user
        drf_request = Request(request)
        drf_request.user = self.user
        return drf_request


class ConsultationCreateSerializerSanitizationTestCase(ConsultationSerializerTestCase):
    """Tests for sanitization in ConsultationCreateSerializer."""

    def test_chief_complaint_sanitizes_script_tags(self):
        """Script tags in chief_complaint should be removed."""
        data = {
            "patient": self.patient.id,
            "chief_complaint": "<script>alert('xss')</script>Headache",
        }
        serializer = ConsultationCreateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["chief_complaint"], "Headache")

    def test_chief_complaint_sanitizes_onclick(self):
        """onclick handlers in chief_complaint should be removed."""
        data = {
            "patient": self.patient.id,
            "chief_complaint": '<div onclick="evil()">Fever</div>',
        }
        serializer = ConsultationCreateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("onclick", serializer.validated_data["chief_complaint"])
        self.assertIn("Fever", serializer.validated_data["chief_complaint"])

    def test_chief_complaint_preserves_plain_text(self):
        """Plain text chief_complaint should remain unchanged."""
        data = {
            "patient": self.patient.id,
            "chief_complaint": "Patient reports headache for 3 days",
        }
        serializer = ConsultationCreateSerializer(
            data=data, context={"request": self.get_mock_request()}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["chief_complaint"],
            "Patient reports headache for 3 days",
        )


class ConsultationBasicUpdateSerializerSanitizationTestCase(ConsultationSerializerTestCase):
    """Tests for sanitization in ConsultationBasicUpdateSerializer."""

    def test_chief_complaint_sanitizes_script_tags(self):
        """Script tags in chief_complaint should be removed."""
        data = {"chief_complaint": "<script>alert('xss')</script>Back pain"}
        serializer = ConsultationBasicUpdateSerializer(
            self.consultation, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["chief_complaint"], "Back pain")

    def test_chief_complaint_sanitizes_html_tags(self):
        """HTML tags in chief_complaint should be removed."""
        data = {"chief_complaint": "<b>Severe</b> <i>headache</i>"}
        serializer = ConsultationBasicUpdateSerializer(
            self.consultation, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["chief_complaint"], "Severe headache")


class ConsultationSOAPUpdateSerializerSanitizationTestCase(ConsultationSerializerTestCase):
    """Tests for sanitization in ConsultationSOAPUpdateSerializer."""

    def test_soap_subjective_sanitizes_script_tags(self):
        """Script tags in soap_subjective should be removed."""
        data = {"soap_subjective": "<script>evil()</script>Patient reports pain"}
        serializer = ConsultationSOAPUpdateSerializer(
            self.consultation, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["soap_subjective"], "Patient reports pain"
        )

    def test_soap_objective_sanitizes_script_tags(self):
        """Script tags in soap_objective should be removed."""
        data = {"soap_objective": "<script>evil()</script>Vitals normal"}
        serializer = ConsultationSOAPUpdateSerializer(
            self.consultation, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["soap_objective"], "Vitals normal")

    def test_soap_assessment_sanitizes_script_tags(self):
        """Script tags in soap_assessment should be removed."""
        data = {"soap_assessment": "<script>evil()</script>Migraine"}
        serializer = ConsultationSOAPUpdateSerializer(
            self.consultation, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["soap_assessment"], "Migraine")

    def test_soap_plan_sanitizes_script_tags(self):
        """Script tags in soap_plan should be removed."""
        data = {"soap_plan": "<script>evil()</script>Prescribe medication"}
        serializer = ConsultationSOAPUpdateSerializer(
            self.consultation, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["soap_plan"], "Prescribe medication"
        )

    def test_all_soap_fields_sanitized_together(self):
        """All SOAP fields should be sanitized when updated together."""
        data = {
            "soap_subjective": "<script>x</script>Subjective note",
            "soap_objective": "<img onerror='x'>Objective note",
            "soap_assessment": "<a href='javascript:x'>Assessment</a>",
            "soap_plan": "<div onclick='x'>Plan note</div>",
        }
        serializer = ConsultationSOAPUpdateSerializer(
            self.consultation, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["soap_subjective"], "Subjective note"
        )
        self.assertNotIn("onerror", serializer.validated_data["soap_objective"])
        self.assertNotIn("javascript", serializer.validated_data["soap_assessment"])
        self.assertNotIn("onclick", serializer.validated_data["soap_plan"])

    def test_soap_fields_preserve_plain_text(self):
        """Plain text SOAP notes should remain unchanged."""
        data = {
            "soap_subjective": "Patient complains of headache",
            "soap_objective": "BP: 120/80, Temp: 98.6F",
            "soap_assessment": "Tension headache",
            "soap_plan": "Rest, hydration, OTC pain relief",
        }
        serializer = ConsultationSOAPUpdateSerializer(
            self.consultation, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["soap_subjective"],
            "Patient complains of headache",
        )
        self.assertEqual(
            serializer.validated_data["soap_objective"], "BP: 120/80, Temp: 98.6F"
        )
        self.assertEqual(
            serializer.validated_data["soap_assessment"], "Tension headache"
        )
        self.assertEqual(
            serializer.validated_data["soap_plan"], "Rest, hydration, OTC pain relief"
        )


class ConsultationFollowUpUpdateSerializerSanitizationTestCase(ConsultationSerializerTestCase):
    """Tests for sanitization in ConsultationFollowUpUpdateSerializer."""

    def test_follow_up_notes_sanitizes_script_tags(self):
        """Script tags in follow_up_notes should be removed."""
        data = {"follow_up_notes": "<script>evil()</script>Return in 2 weeks"}
        serializer = ConsultationFollowUpUpdateSerializer(
            self.consultation, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["follow_up_notes"], "Return in 2 weeks"
        )

    def test_follow_up_notes_sanitizes_html_tags(self):
        """HTML tags in follow_up_notes should be removed."""
        data = {
            "follow_up_notes": "<b>Important:</b> Follow up in <i>one</i> week"
        }
        serializer = ConsultationFollowUpUpdateSerializer(
            self.consultation, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["follow_up_notes"],
            "Important: Follow up in one week",
        )

    def test_follow_up_notes_preserves_plain_text(self):
        """Plain text follow_up_notes should remain unchanged."""
        data = {"follow_up_notes": "Schedule follow-up appointment in 2 weeks"}
        serializer = ConsultationFollowUpUpdateSerializer(
            self.consultation, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["follow_up_notes"],
            "Schedule follow-up appointment in 2 weeks",
        )


class ConsultationAdminTestCase(TestCase):
    """Tests for the Consultation admin configuration."""

    def setUp(self):
        """Set up test fixtures."""
        from django.contrib.admin.sites import AdminSite

        from apps.consultations.admin import ConsultationAdmin

        self.site = AdminSite()
        self.admin = ConsultationAdmin(Consultation, self.site)

    def test_list_display_fields_exist(self):
        """All fields in list_display should exist on the model."""
        for field in self.admin.list_display:
            if field == "__str__":
                continue
            self.assertTrue(
                hasattr(Consultation, field) or hasattr(self.admin, field),
                f"Field '{field}' in list_display does not exist on Consultation model",
            )

    def test_list_filter_fields_exist(self):
        """All fields in list_filter should exist on the model."""
        for field in self.admin.list_filter:
            self.assertTrue(
                hasattr(Consultation, field),
                f"Field '{field}' in list_filter does not exist on Consultation model",
            )

    def test_search_fields_valid(self):
        """All fields in search_fields should be valid."""
        for field in self.admin.search_fields:
            # Handle related field lookups like patient__first_name
            base_field = field.split("__")[0]
            self.assertTrue(
                hasattr(Consultation, base_field),
                f"Field '{base_field}' in search_fields does not exist on Consultation model",
            )

    def test_readonly_fields_exist(self):
        """All readonly_fields should exist on the model."""
        for field in self.admin.readonly_fields:
            self.assertTrue(
                hasattr(Consultation, field),
                f"Field '{field}' in readonly_fields does not exist on Consultation model",
            )
