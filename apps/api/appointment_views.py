"""
API views for Appointment CRUD operations.
"""

from datetime import datetime

from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsAuthenticatedWithClinicAccess
from apps.appointments.models import Appointment
from apps.appointments.serializers import AppointmentCreateUpdateSerializer, AppointmentSerializer


def generate_appointment_id(clinic):
    """
    Generate a unique appointment ID for the clinic.
    Format: APT-YYYY-####
    """
    year = datetime.now().year
    prefix = f"APT-{year}-"

    # Get the max appointment_id for this clinic and year
    last_appointment = Appointment.objects.filter(clinic=clinic, appointment_id__startswith=prefix).aggregate(
        max_id=Max("appointment_id")
    )

    if last_appointment["max_id"]:
        # Extract the sequence number and increment
        last_seq = int(last_appointment["max_id"].split("-")[-1])
        new_seq = last_seq + 1
    else:
        new_seq = 1

    return f"{prefix}{new_seq:04d}"


class AppointmentListCreateView(APIView):
    """
    GET: List all appointments for the clinic.
    POST: Create a new appointment.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get(self, request):
        """List all appointments for the clinic."""
        clinic = request.user.clinic
        appointments = Appointment.objects.filter(clinic=clinic).select_related("patient", "service", "assigned_to")
        return Response(
            {
                "success": True,
                "appointments": AppointmentSerializer(appointments, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new appointment."""
        clinic = request.user.clinic
        serializer = AppointmentCreateUpdateSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            # Generate appointment_id
            appointment_id = generate_appointment_id(clinic)
            appointment = serializer.save(clinic=clinic, appointment_id=appointment_id)
            return Response(
                {
                    "success": True,
                    "appointment": AppointmentSerializer(appointment).data,
                    "message": _("Appointment created successfully"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class AppointmentDetailView(APIView):
    """
    GET: Get appointment details.
    PUT: Update an appointment.
    DELETE: Delete an appointment.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get_object(self, pk, request):
        """Get appointment by ID, ensuring it belongs to user's clinic."""
        return get_object_or_404(
            Appointment.objects.select_related("patient", "service", "assigned_to"),
            pk=pk,
            clinic=request.user.clinic,
        )

    def get(self, request, pk):
        """Get appointment details."""
        appointment = self.get_object(pk, request)
        return Response(
            {
                "success": True,
                "appointment": AppointmentSerializer(appointment).data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        """Update an appointment."""
        appointment = self.get_object(pk, request)

        serializer = AppointmentCreateUpdateSerializer(
            appointment,
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            appointment = serializer.save()
            return Response(
                {
                    "success": True,
                    "appointment": AppointmentSerializer(appointment).data,
                    "message": _("Appointment updated successfully"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        """Delete an appointment."""
        appointment = self.get_object(pk, request)
        appointment.delete()

        return Response(
            {
                "success": True,
                "message": _("Appointment deleted successfully"),
            },
            status=status.HTTP_200_OK,
        )
