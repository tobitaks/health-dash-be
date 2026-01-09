"""
API views for Prescription CRUD operations.
"""

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsAuthenticatedWithClinicAccess
from apps.consultations.models import Consultation
from apps.prescriptions.models import Prescription
from apps.prescriptions.serializers import (
    PrescriptionCreateUpdateSerializer,
    PrescriptionSerializer,
)


class PrescriptionListCreateView(APIView):
    """
    GET: List all prescriptions for the clinic.
    POST: Create a new prescription.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get(self, request):
        """List all prescriptions for the clinic."""
        clinic = request.user.clinic

        # Filter options
        patient_id = request.query_params.get("patient_id")
        consultation_id = request.query_params.get("consultation_id")
        status_filter = request.query_params.get("status")

        prescriptions = (
            Prescription.objects.filter(clinic=clinic)
            .select_related("patient", "consultation", "prescribed_by")
            .prefetch_related("items")
        )

        if patient_id:
            prescriptions = prescriptions.filter(patient_id=patient_id)

        if consultation_id:
            prescriptions = prescriptions.filter(consultation_id=consultation_id)

        if status_filter:
            prescriptions = prescriptions.filter(status=status_filter)

        return Response(
            {
                "success": True,
                "prescriptions": PrescriptionSerializer(prescriptions, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new prescription."""
        clinic = request.user.clinic

        # Validate consultation belongs to clinic
        consultation_id = request.data.get("consultation")
        if consultation_id:
            try:
                consultation = Consultation.objects.get(id=consultation_id, clinic=clinic)
                # Check if prescription already exists for this consultation
                if hasattr(consultation, "prescription"):
                    return Response(
                        {
                            "success": False,
                            "message": _("A prescription already exists for this consultation"),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Consultation.DoesNotExist:
                return Response(
                    {"success": False, "message": _("Consultation not found")},
                    status=status.HTTP_404_NOT_FOUND,
                )

        serializer = PrescriptionCreateUpdateSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            prescription = serializer.save()
            return Response(
                {
                    "success": True,
                    "prescription": PrescriptionSerializer(prescription).data,
                    "message": _("Prescription created successfully"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PrescriptionDetailView(APIView):
    """
    GET: Get prescription details.
    PUT: Update a prescription.
    DELETE: Delete a prescription.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get_object(self, pk, request):
        """Get prescription by ID, ensuring it belongs to user's clinic."""
        return get_object_or_404(
            Prescription.objects.select_related("patient", "consultation", "prescribed_by").prefetch_related("items"),
            pk=pk,
            clinic=request.user.clinic,
        )

    def get(self, request, pk):
        """Get prescription details."""
        prescription = self.get_object(pk, request)
        return Response(
            {
                "success": True,
                "prescription": PrescriptionSerializer(prescription).data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        """Update a prescription."""
        prescription = self.get_object(pk, request)

        serializer = PrescriptionCreateUpdateSerializer(
            prescription,
            data=request.data,
            context={"request": request},
            partial=True,
        )

        if serializer.is_valid():
            prescription = serializer.save()
            return Response(
                {
                    "success": True,
                    "prescription": PrescriptionSerializer(prescription).data,
                    "message": _("Prescription updated successfully"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        """Delete a prescription."""
        prescription = self.get_object(pk, request)
        prescription.delete()

        return Response(
            {
                "success": True,
                "message": _("Prescription deleted successfully"),
            },
            status=status.HTTP_200_OK,
        )


class ConsultationPrescriptionView(APIView):
    """
    GET: Get prescription for a specific consultation.
    POST: Create prescription for a consultation (if doesn't exist).
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get(self, request, consultation_id):
        """Get prescription for a consultation."""
        clinic = request.user.clinic

        consultation = get_object_or_404(Consultation, id=consultation_id, clinic=clinic)

        try:
            prescription = (
                Prescription.objects.select_related("patient", "consultation", "prescribed_by")
                .prefetch_related("items")
                .get(consultation=consultation)
            )

            return Response(
                {
                    "success": True,
                    "prescription": PrescriptionSerializer(prescription).data,
                },
                status=status.HTTP_200_OK,
            )
        except Prescription.DoesNotExist:
            return Response(
                {
                    "success": True,
                    "prescription": None,
                    "message": _("No prescription for this consultation"),
                },
                status=status.HTTP_200_OK,
            )

    def post(self, request, consultation_id):
        """Create prescription for a consultation."""
        clinic = request.user.clinic

        consultation = get_object_or_404(Consultation, id=consultation_id, clinic=clinic)

        # Check if prescription already exists
        if hasattr(consultation, "prescription"):
            return Response(
                {
                    "success": False,
                    "message": _("A prescription already exists for this consultation"),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Add consultation to request data
        data = request.data.copy()
        data["consultation"] = consultation_id

        serializer = PrescriptionCreateUpdateSerializer(
            data=data,
            context={"request": request},
        )

        if serializer.is_valid():
            prescription = serializer.save()
            return Response(
                {
                    "success": True,
                    "prescription": PrescriptionSerializer(prescription).data,
                    "message": _("Prescription created successfully"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
