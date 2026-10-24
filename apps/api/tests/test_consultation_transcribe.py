"""
Tests for the chief complaint audio transcription endpoint.
"""

from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.clinic.models import Clinic
from apps.consultations.models import Consultation
from apps.patients.models import Patient
from apps.users.models import CustomUser


class FakeTranscription:
    def __init__(self, text):
        self.text = text


def make_audio(name="complaint.webm", content_type="audio/webm", size=1024):
    return SimpleUploadedFile(name, b"\x1a\x45\xdf\xa3" + b"0" * size, content_type=content_type)


@override_settings(OPENAI_API_KEY="test-openai-key")
class TranscribeChiefComplaintViewTestCase(TestCase):
    def setUp(self):
        self.clinic = Clinic.objects.create(name="Test Clinic")
        self.user = CustomUser.objects.create_user(
            username="doc", email="doc@example.com", password="pass12345", clinic=self.clinic
        )
        self.patient = Patient.objects.create(
            clinic=self.clinic,
            patient_id="PT-2026-0001",
            first_name="Jane",
            last_name="Doe",
            date_of_birth="1990-01-15",
            gender="Female",
            phone="09171234567",
        )
        self.consultation = Consultation.objects.create(
            clinic=self.clinic,
            patient=self.patient,
            created_by=self.user,
            consultation_id="CONS-2026-0001",
            consultation_date="2026-10-23",
            consultation_time="10:00:00",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def url(self, pk=None):
        return f"/api/consultations/{pk or self.consultation.pk}/transcribe/"

    @patch("apps.consultations.services.transcription.litellm.transcription")
    def test_returns_transcript_for_uploaded_audio(self, mock_transcription):
        sent = {}

        def capture(**kwargs):
            filename, fileobj, content_type = kwargs["file"]
            sent.update(filename=filename, content_type=content_type, head=fileobj.read(4))
            return FakeTranscription("Patient reports chest pain since Tuesday.")

        mock_transcription.side_effect = capture

        response = self.client.post(self.url(), {"audio": make_audio()}, format="multipart")

        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["transcript"], "Patient reports chest pain since Tuesday.")
        kwargs = mock_transcription.call_args.kwargs
        self.assertEqual(kwargs["language"], "en")
        self.assertEqual(kwargs["api_key"], "test-openai-key")
        self.assertEqual(sent["filename"], "complaint.webm")
        self.assertEqual(sent["content_type"], "audio/webm")
        self.assertEqual(sent["head"], b"\x1a\x45\xdf\xa3")

    def test_requires_authentication(self):
        response = APIClient().post(self.url(), {"audio": make_audio()}, format="multipart")
        self.assertEqual(response.status_code, 401)

    @patch("apps.consultations.services.transcription.litellm.transcription")
    def test_other_clinic_consultation_returns_404(self, mock_transcription):
        other_clinic = Clinic.objects.create(name="Other Clinic")
        other_user = CustomUser.objects.create_user(
            username="other", email="other@example.com", password="pass12345", clinic=other_clinic
        )
        other_patient = Patient.objects.create(
            clinic=other_clinic,
            patient_id="PT-2026-0002",
            first_name="Max",
            last_name="Roe",
            date_of_birth="1985-05-05",
            gender="Male",
            phone="09170000000",
        )
        other_consultation = Consultation.objects.create(
            clinic=other_clinic,
            patient=other_patient,
            created_by=other_user,
            consultation_id="CONS-2026-0002",
            consultation_date="2026-10-23",
            consultation_time="11:00:00",
        )

        response = self.client.post(self.url(other_consultation.pk), {"audio": make_audio()}, format="multipart")

        self.assertEqual(response.status_code, 404)
        mock_transcription.assert_not_called()

    @patch("apps.consultations.services.transcription.litellm.transcription")
    def test_missing_audio_returns_400(self, mock_transcription):
        response = self.client.post(self.url(), {}, format="multipart")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        mock_transcription.assert_not_called()

    @patch("apps.consultations.services.transcription.litellm.transcription")
    def test_oversized_audio_returns_400(self, mock_transcription):
        big = make_audio(size=25 * 1024 * 1024 + 1)

        response = self.client.post(self.url(), {"audio": big}, format="multipart")

        self.assertEqual(response.status_code, 400)
        mock_transcription.assert_not_called()

    @override_settings(OPENAI_API_KEY="")
    @patch("apps.consultations.services.transcription.litellm.transcription")
    def test_missing_api_key_returns_503(self, mock_transcription):
        response = self.client.post(self.url(), {"audio": make_audio()}, format="multipart")

        self.assertEqual(response.status_code, 503)
        mock_transcription.assert_not_called()

    @patch("apps.consultations.services.transcription.litellm.transcription")
    def test_provider_failure_returns_500(self, mock_transcription):
        mock_transcription.side_effect = RuntimeError("provider down")

        response = self.client.post(self.url(), {"audio": make_audio()}, format="multipart")

        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.data["success"])
