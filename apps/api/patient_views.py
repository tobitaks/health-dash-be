"""
API views for Patient CRUD operations.
"""

from datetime import datetime

from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsAuthenticatedWithClinicAccess
from apps.patients.models import Patient
from apps.patients.serializers import PatientCreateUpdateSerializer, PatientSerializer


def generate_patient_id(clinic):
    """
    Generate a unique patient ID for the clinic.
    Format: PT-YYYY-####
    """
    year = datetime.now().year
    prefix = f"PT-{year}-"

    # Get the max patient_id for this clinic and year
    last_patient = Patient.objects.filter(clinic=clinic, patient_id__startswith=prefix).aggregate(
        max_id=Max("patient_id")
    )

    if last_patient["max_id"]:
        # Extract the sequence number and increment
        last_seq = int(last_patient["max_id"].split("-")[-1])
        new_seq = last_seq + 1
    else:
        new_seq = 1

    return f"{prefix}{new_seq:04d}"


class PatientListCreateView(APIView):
    """
    GET: List all patients for the clinic.
    POST: Create a new patient.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get(self, request):
        """List all patients for the clinic."""
        clinic = request.user.clinic
        patients = Patient.objects.filter(clinic=clinic)
        return Response(
            {
                "success": True,
                "patients": PatientSerializer(patients, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new patient."""
        clinic = request.user.clinic
        serializer = PatientCreateUpdateSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            # Generate patient_id
            patient_id = generate_patient_id(clinic)
            patient = serializer.save(clinic=clinic, patient_id=patient_id)
            return Response(
                {
                    "success": True,
                    "patient": PatientSerializer(patient).data,
                    "message": _("Patient created successfully"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PatientDetailView(APIView):
    """
    GET: Get patient details.
    PUT: Update a patient.
    DELETE: Delete a patient.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get_object(self, pk, request):
        """Get patient by ID, ensuring it belongs to user's clinic."""
        return get_object_or_404(Patient, pk=pk, clinic=request.user.clinic)

    def get(self, request, pk):
        """Get patient details."""
        patient = self.get_object(pk, request)
        return Response(
            {
                "success": True,
                "patient": PatientSerializer(patient).data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        """Update a patient."""
        patient = self.get_object(pk, request)

        serializer = PatientCreateUpdateSerializer(
            patient,
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            patient = serializer.save()
            return Response(
                {
                    "success": True,
                    "patient": PatientSerializer(patient).data,
                    "message": _("Patient updated successfully"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        """Delete a patient."""
        patient = self.get_object(pk, request)
        patient.delete()

        return Response(
            {
                "success": True,
                "message": _("Patient deleted successfully"),
            },
            status=status.HTTP_200_OK,
        )
