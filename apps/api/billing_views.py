"""
API views for Invoice CRUD operations.
"""

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Invoice, InvoiceItem
from apps.billing.serializers import (
    InvoiceSerializer,
    InvoiceCreateUpdateSerializer,
    InvoicePaySerializer,
    InvoiceFinalizeSerializer,
    InvoiceCancelSerializer,
)
from apps.consultations.models import Consultation


class InvoiceListCreateView(APIView):
    """
    GET: List all invoices for the clinic.
    POST: Create a new invoice.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all invoices for the clinic."""
        clinic = request.user.clinic
        if not clinic:
            return Response(
                {"success": False, "message": _("User has no clinic")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filter options
        patient_id = request.query_params.get("patient_id")
        consultation_id = request.query_params.get("consultation_id")
        status_filter = request.query_params.get("status")

        invoices = Invoice.objects.filter(clinic=clinic).select_related(
            "patient", "consultation", "created_by"
        ).prefetch_related("items")

        if patient_id:
            invoices = invoices.filter(patient_id=patient_id)

        if consultation_id:
            invoices = invoices.filter(consultation_id=consultation_id)

        if status_filter:
            invoices = invoices.filter(status=status_filter)

        return Response(
            {
                "success": True,
                "invoices": InvoiceSerializer(invoices, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new invoice."""
        clinic = request.user.clinic
        if not clinic:
            return Response(
                {"success": False, "message": _("User has no clinic")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate consultation belongs to clinic
        consultation_id = request.data.get("consultation")
        if consultation_id:
            try:
                consultation = Consultation.objects.get(id=consultation_id, clinic=clinic)
                # Check if invoice already exists for this consultation
                if hasattr(consultation, "invoice"):
                    return Response(
                        {
                            "success": False,
                            "message": _("An invoice already exists for this consultation"),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Consultation.DoesNotExist:
                return Response(
                    {"success": False, "message": _("Consultation not found")},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            return Response(
                {"success": False, "message": _("Consultation is required")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InvoiceCreateUpdateSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            invoice = serializer.save()
            return Response(
                {
                    "success": True,
                    "invoice": InvoiceSerializer(invoice).data,
                    "message": _("Invoice created successfully"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class InvoiceDetailView(APIView):
    """
    GET: Get invoice details.
    PUT: Update an invoice.
    DELETE: Delete an invoice.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        """Get invoice by ID, ensuring it belongs to user's clinic."""
        return get_object_or_404(
            Invoice.objects.select_related(
                "patient", "consultation", "created_by"
            ).prefetch_related("items"),
            pk=pk,
            clinic=request.user.clinic,
        )

    def get(self, request, pk):
        """Get invoice details."""
        invoice = self.get_object(pk, request)
        return Response(
            {
                "success": True,
                "invoice": InvoiceSerializer(invoice).data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        """Update an invoice (only if draft)."""
        invoice = self.get_object(pk, request)

        if invoice.status != "draft":
            return Response(
                {
                    "success": False,
                    "message": _("Only draft invoices can be edited"),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InvoiceCreateUpdateSerializer(
            invoice,
            data=request.data,
            context={"request": request},
            partial=True,
        )

        if serializer.is_valid():
            invoice = serializer.save()
            return Response(
                {
                    "success": True,
                    "invoice": InvoiceSerializer(invoice).data,
                    "message": _("Invoice updated successfully"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        """Delete an invoice (only if draft)."""
        invoice = self.get_object(pk, request)

        if invoice.status != "draft":
            return Response(
                {
                    "success": False,
                    "message": _("Only draft invoices can be deleted"),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice.delete()

        return Response(
            {
                "success": True,
                "message": _("Invoice deleted successfully"),
            },
            status=status.HTTP_200_OK,
        )


class ConsultationInvoiceView(APIView):
    """
    GET: Get invoice for a specific consultation.
    POST: Create invoice for a consultation with auto-populated service.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, consultation_id):
        """Get invoice for a consultation."""
        clinic = request.user.clinic
        if not clinic:
            return Response(
                {"success": False, "message": _("User has no clinic")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        consultation = get_object_or_404(Consultation, id=consultation_id, clinic=clinic)

        try:
            invoice = Invoice.objects.select_related(
                "patient", "consultation", "created_by"
            ).prefetch_related("items").get(consultation=consultation)

            return Response(
                {
                    "success": True,
                    "invoice": InvoiceSerializer(invoice).data,
                },
                status=status.HTTP_200_OK,
            )
        except Invoice.DoesNotExist:
            return Response(
                {
                    "success": True,
                    "invoice": None,
                    "message": _("No invoice for this consultation"),
                },
                status=status.HTTP_200_OK,
            )

    def post(self, request, consultation_id):
        """Create invoice for a consultation with auto-populated service."""
        from datetime import date
        from decimal import Decimal

        clinic = request.user.clinic
        if not clinic:
            return Response(
                {"success": False, "message": _("User has no clinic")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        consultation = get_object_or_404(
            Consultation.objects.select_related("appointment__service"),
            id=consultation_id,
            clinic=clinic,
        )

        # Check if invoice already exists
        if hasattr(consultation, "invoice"):
            return Response(
                {
                    "success": False,
                    "message": _("An invoice already exists for this consultation"),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prepare data with auto-populated items
        data = request.data.copy() if request.data else {}
        data["consultation"] = consultation_id

        # If no items provided and consultation has appointment with service, auto-add
        if "items" not in data or not data["items"]:
            items = []
            if consultation.appointment and consultation.appointment.service:
                service = consultation.appointment.service
                items.append({
                    "service_id": service.id,
                    "description": service.name,
                    "quantity": 1,
                    "unit_price": str(service.price),
                })
            data["items"] = items

        # Set defaults
        if "invoice_date" not in data:
            data["invoice_date"] = date.today().isoformat()
        if "discount_type" not in data:
            data["discount_type"] = "none"
        if "discount_value" not in data:
            data["discount_value"] = "0"

        serializer = InvoiceCreateUpdateSerializer(
            data=data,
            context={"request": request},
        )

        if serializer.is_valid():
            invoice = serializer.save()
            return Response(
                {
                    "success": True,
                    "invoice": InvoiceSerializer(invoice).data,
                    "message": _("Invoice created successfully"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class InvoicePayView(APIView):
    """
    PATCH: Record payment for an invoice.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        """Record payment - marks invoice as paid."""
        invoice = get_object_or_404(
            Invoice,
            pk=pk,
            clinic=request.user.clinic,
        )

        serializer = InvoicePaySerializer(
            invoice,
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            invoice = serializer.save()
            return Response(
                {
                    "success": True,
                    "invoice": InvoiceSerializer(invoice).data,
                    "message": _("Payment recorded successfully"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class InvoiceFinalizeView(APIView):
    """
    PATCH: Finalize invoice (draft -> pending).
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        """Finalize invoice - move from draft to pending."""
        invoice = get_object_or_404(
            Invoice,
            pk=pk,
            clinic=request.user.clinic,
        )

        serializer = InvoiceFinalizeSerializer(
            invoice,
            data={},
            context={"request": request},
        )

        if serializer.is_valid():
            invoice = serializer.save()
            return Response(
                {
                    "success": True,
                    "invoice": InvoiceSerializer(invoice).data,
                    "message": _("Invoice finalized successfully"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class InvoiceCancelView(APIView):
    """
    PATCH: Cancel an invoice.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        """Cancel an invoice."""
        invoice = get_object_or_404(
            Invoice,
            pk=pk,
            clinic=request.user.clinic,
        )

        serializer = InvoiceCancelSerializer(
            invoice,
            data={},
            context={"request": request},
        )

        if serializer.is_valid():
            invoice = serializer.save()
            return Response(
                {
                    "success": True,
                    "invoice": InvoiceSerializer(invoice).data,
                    "message": _("Invoice cancelled successfully"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UnbilledConsultationsView(APIView):
    """
    GET: List all consultations that don't have an invoice.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get consultations without invoices."""
        clinic = request.user.clinic
        if not clinic:
            return Response(
                {"success": False, "message": _("User has no clinic")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get consultations that don't have an invoice
        consultations = Consultation.objects.filter(
            clinic=clinic,
        ).exclude(
            invoice__isnull=False
        ).select_related(
            "patient", "appointment__service"
        ).order_by("-consultation_date", "-consultation_time")

        # Build response data
        data = []
        for consultation in consultations:
            service_name = None
            service_price = None
            if consultation.appointment and consultation.appointment.service:
                service_name = consultation.appointment.service.name
                service_price = float(consultation.appointment.service.price)

            data.append({
                "id": consultation.id,
                "consultation_id": consultation.consultation_id,
                "consultation_date": consultation.consultation_date,
                "consultation_time": str(consultation.consultation_time) if consultation.consultation_time else None,
                "patient_id": consultation.patient_id,
                "patient_name": consultation.patient.full_name if consultation.patient else None,
                "service_name": service_name,
                "service_price": service_price,
                "status": consultation.status,
            })

        return Response(
            {
                "success": True,
                "consultations": data,
            },
            status=status.HTTP_200_OK,
        )
