"""
API views for Consultation CRUD operations.
"""

import logging
from datetime import datetime

from asgiref.sync import async_to_sync
from django.conf import settings
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.consultations.models import Consultation
from apps.consultations.serializers import (
    ConsultationCreateSerializer,
    ConsultationSerializer,
    ConsultationUpdateSerializer,
)
from apps.consultations.services import build_soap_context, generate_soap_with_ai

logger = logging.getLogger(__name__)


def generate_consultation_id(clinic):
    """
    Generate a unique consultation ID for the clinic.
    Format: CONS-YYYY-####
    """
    year = datetime.now().year
    prefix = f"CONS-{year}-"

    # Get the max consultation_id for this clinic and year
    last_consultation = Consultation.objects.filter(
        clinic=clinic, consultation_id__startswith=prefix
    ).aggregate(max_id=Max("consultation_id"))

    if last_consultation["max_id"]:
        # Extract the sequence number and increment
        last_seq = int(last_consultation["max_id"].split("-")[-1])
        new_seq = last_seq + 1
    else:
        new_seq = 1

    return f"{prefix}{new_seq:04d}"


class ConsultationListCreateView(APIView):
    """
    GET: List all consultations for the clinic.
    POST: Create a new consultation.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all consultations for the clinic."""
        clinic = request.user.clinic
        if not clinic:
            return Response(
                {"success": False, "message": _("User has no clinic")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        consultations = Consultation.objects.filter(clinic=clinic).select_related(
            "patient", "appointment", "created_by"
        )
        return Response(
            {
                "success": True,
                "consultations": ConsultationSerializer(consultations, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new consultation."""
        clinic = request.user.clinic
        if not clinic:
            return Response(
                {"success": False, "message": _("User has no clinic")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ConsultationCreateSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            # Generate consultation_id
            consultation_id = generate_consultation_id(clinic)
            consultation = serializer.save(
                clinic=clinic,
                consultation_id=consultation_id,
                created_by=request.user,
                status="draft",
            )
            return Response(
                {
                    "success": True,
                    "consultation": ConsultationSerializer(consultation).data,
                    "message": _("Consultation created successfully"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ConsultationDetailView(APIView):
    """
    GET: Get consultation details.
    PUT: Update a consultation.
    DELETE: Delete a consultation.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        """Get consultation by ID, ensuring it belongs to user's clinic."""
        return get_object_or_404(
            Consultation.objects.select_related("patient", "appointment", "created_by"),
            pk=pk,
            clinic=request.user.clinic,
        )

    def get(self, request, pk):
        """Get consultation details."""
        consultation = self.get_object(pk, request)
        return Response(
            {
                "success": True,
                "consultation": ConsultationSerializer(consultation).data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        """Update a consultation."""
        consultation = self.get_object(pk, request)

        serializer = ConsultationUpdateSerializer(
            consultation,
            data=request.data,
            partial=True,  # Allow partial updates
            context={"request": request},
        )

        if serializer.is_valid():
            consultation = serializer.save()
            return Response(
                {
                    "success": True,
                    "consultation": ConsultationSerializer(consultation).data,
                    "message": _("Consultation updated successfully"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        """Delete a consultation."""
        consultation = self.get_object(pk, request)
        consultation.delete()

        return Response(
            {
                "success": True,
                "message": _("Consultation deleted successfully"),
            },
            status=status.HTTP_200_OK,
        )


class GenerateSOAPView(APIView):
    """
    POST: Generate SOAP notes using AI based on consultation data.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Generate SOAP notes using AI."""
        clinic = request.user.clinic
        if not clinic:
            return Response(
                {"success": False, "message": _("User has no clinic")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if AI is configured (any LLM provider)
        has_openai = getattr(settings, "OPENAI_API_KEY", "") or ""
        has_anthropic = getattr(settings, "ANTHROPIC_API_KEY", "") or ""
        if not has_openai and not has_anthropic:
            return Response(
                {
                    "success": False,
                    "message": _("AI service is not configured. Please contact administrator."),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Get the consultation
        consultation = get_object_or_404(
            Consultation.objects.select_related("patient"),
            pk=pk,
            clinic=clinic,
        )

        # Check if consultation has required data
        if not consultation.chief_complaint:
            return Response(
                {
                    "success": False,
                    "message": _("Chief complaint is required to generate SOAP notes."),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get patient history (previous consultations)
        patient_history = (
            Consultation.objects.filter(
                patient=consultation.patient,
                clinic=clinic,
            )
            .exclude(pk=pk)
            .order_by("-consultation_date")[:5]
        )

        # Build context for AI
        context = build_soap_context(consultation, patient_history)

        try:
            # Call AI service (async function wrapped for sync Django)
            soap_result = async_to_sync(generate_soap_with_ai)(context)

            return Response(
                {
                    "success": True,
                    "soap": soap_result,
                    "context_used": context,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Error generating SOAP notes with AI")
            return Response(
                {
                    "success": False,
                    "message": _("Failed to generate SOAP notes. Please try again."),
                    "error": str(e) if settings.DEBUG else None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
