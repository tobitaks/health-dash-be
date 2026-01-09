"""
API views for Lab Order CRUD operations.
"""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsAuthenticatedWithClinicAccess
from apps.consultations.models import Consultation
from apps.lab_orders.models import LabOrder, LabOrderItem, LabTest
from apps.lab_orders.serializers import (
    LabOrderCreateUpdateSerializer,
    LabOrderItemResultSerializer,
    LabOrderSerializer,
    LabTestCreateUpdateSerializer,
    LabTestSerializer,
)

# =============================================================================
# Lab Test Views (Catalog Management)
# =============================================================================


class LabTestListCreateView(APIView):
    """
    GET: List all lab tests in the clinic's catalog.
    POST: Create a new lab test.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get(self, request):
        """List all lab tests for the clinic."""
        clinic = request.user.clinic

        # Filter options
        category = request.query_params.get("category")
        sample_type = request.query_params.get("sample_type")
        is_active = request.query_params.get("is_active")
        search = request.query_params.get("search")

        lab_tests = LabTest.objects.filter(clinic=clinic)

        if category:
            lab_tests = lab_tests.filter(category=category)

        if sample_type:
            lab_tests = lab_tests.filter(sample_type=sample_type)

        if is_active is not None:
            lab_tests = lab_tests.filter(is_active=is_active.lower() == "true")

        if search:
            lab_tests = lab_tests.filter(name__icontains=search) | lab_tests.filter(code__icontains=search)

        return Response(
            {
                "success": True,
                "lab_tests": LabTestSerializer(lab_tests, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new lab test."""
        clinic = request.user.clinic

        serializer = LabTestCreateUpdateSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            lab_test = serializer.save(clinic=clinic)
            return Response(
                {
                    "success": True,
                    "lab_test": LabTestSerializer(lab_test).data,
                    "message": _("Lab test created successfully"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LabTestDetailView(APIView):
    """
    GET: Get lab test details.
    PUT: Update a lab test.
    DELETE: Delete a lab test.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get_object(self, pk, request):
        """Get lab test by ID, ensuring it belongs to user's clinic."""
        return get_object_or_404(LabTest, pk=pk, clinic=request.user.clinic)

    def get(self, request, pk):
        """Get lab test details."""
        lab_test = self.get_object(pk, request)
        return Response(
            {
                "success": True,
                "lab_test": LabTestSerializer(lab_test).data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        """Update a lab test."""
        lab_test = self.get_object(pk, request)

        serializer = LabTestCreateUpdateSerializer(
            lab_test,
            data=request.data,
            context={"request": request},
            partial=True,
        )

        if serializer.is_valid():
            lab_test = serializer.save()
            return Response(
                {
                    "success": True,
                    "lab_test": LabTestSerializer(lab_test).data,
                    "message": _("Lab test updated successfully"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        """Delete a lab test."""
        lab_test = self.get_object(pk, request)
        lab_test.delete()

        return Response(
            {
                "success": True,
                "message": _("Lab test deleted successfully"),
            },
            status=status.HTTP_200_OK,
        )


# =============================================================================
# Lab Order Views
# =============================================================================


class LabOrderListCreateView(APIView):
    """
    GET: List all lab orders for the clinic.
    POST: Create a new lab order.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get(self, request):
        """List all lab orders for the clinic."""
        clinic = request.user.clinic

        # Filter options
        patient_id = request.query_params.get("patient_id")
        consultation_id = request.query_params.get("consultation_id")
        status_filter = request.query_params.get("status")
        priority = request.query_params.get("priority")

        lab_orders = (
            LabOrder.objects.filter(clinic=clinic)
            .select_related("patient", "consultation", "ordered_by")
            .prefetch_related("items")
        )

        if patient_id:
            lab_orders = lab_orders.filter(patient_id=patient_id)

        if consultation_id:
            lab_orders = lab_orders.filter(consultation_id=consultation_id)

        if status_filter:
            lab_orders = lab_orders.filter(status=status_filter)

        if priority:
            lab_orders = lab_orders.filter(priority=priority)

        return Response(
            {
                "success": True,
                "lab_orders": LabOrderSerializer(lab_orders, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new lab order."""
        clinic = request.user.clinic

        # Validate consultation belongs to clinic
        consultation_id = request.data.get("consultation")
        if consultation_id:
            try:
                Consultation.objects.get(id=consultation_id, clinic=clinic)
            except Consultation.DoesNotExist:
                return Response(
                    {"success": False, "message": _("Consultation not found")},
                    status=status.HTTP_404_NOT_FOUND,
                )

        serializer = LabOrderCreateUpdateSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            lab_order = serializer.save()
            return Response(
                {
                    "success": True,
                    "lab_order": LabOrderSerializer(lab_order).data,
                    "message": _("Lab order created successfully"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LabOrderDetailView(APIView):
    """
    GET: Get lab order details.
    PUT: Update a lab order.
    DELETE: Delete a lab order.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get_object(self, pk, request):
        """Get lab order by ID, ensuring it belongs to user's clinic."""
        return get_object_or_404(
            LabOrder.objects.select_related("patient", "consultation", "ordered_by").prefetch_related("items"),
            pk=pk,
            clinic=request.user.clinic,
        )

    def get(self, request, pk):
        """Get lab order details."""
        lab_order = self.get_object(pk, request)
        return Response(
            {
                "success": True,
                "lab_order": LabOrderSerializer(lab_order).data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        """Update a lab order."""
        lab_order = self.get_object(pk, request)

        serializer = LabOrderCreateUpdateSerializer(
            lab_order,
            data=request.data,
            context={"request": request},
            partial=True,
        )

        if serializer.is_valid():
            lab_order = serializer.save()
            return Response(
                {
                    "success": True,
                    "lab_order": LabOrderSerializer(lab_order).data,
                    "message": _("Lab order updated successfully"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        """Delete a lab order."""
        lab_order = self.get_object(pk, request)
        lab_order.delete()

        return Response(
            {
                "success": True,
                "message": _("Lab order deleted successfully"),
            },
            status=status.HTTP_200_OK,
        )


class LabOrderStatusView(APIView):
    """
    PATCH: Update lab order status.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def patch(self, request, pk):
        """Update lab order status."""
        clinic = request.user.clinic

        lab_order = get_object_or_404(LabOrder, pk=pk, clinic=clinic)
        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"success": False, "message": _("Status is required")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_statuses = [choice[0] for choice in LabOrder.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {"success": False, "message": _("Invalid status")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lab_order.status = new_status
        lab_order.save()

        return Response(
            {
                "success": True,
                "lab_order": LabOrderSerializer(lab_order).data,
                "message": _("Lab order status updated successfully"),
            },
            status=status.HTTP_200_OK,
        )


class ConsultationLabOrdersView(APIView):
    """
    GET: Get all lab orders for a specific consultation.
    POST: Create a lab order for a consultation.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get(self, request, consultation_id):
        """Get all lab orders for a consultation."""
        clinic = request.user.clinic

        consultation = get_object_or_404(Consultation, id=consultation_id, clinic=clinic)

        lab_orders = (
            LabOrder.objects.filter(consultation=consultation)
            .select_related("patient", "consultation", "ordered_by")
            .prefetch_related("items")
        )

        return Response(
            {
                "success": True,
                "lab_orders": LabOrderSerializer(lab_orders, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, consultation_id):
        """Create a lab order for a consultation."""
        clinic = request.user.clinic

        consultation = get_object_or_404(Consultation, id=consultation_id, clinic=clinic)

        # Add consultation to request data
        data = request.data.copy()
        data["consultation"] = consultation_id

        serializer = LabOrderCreateUpdateSerializer(
            data=data,
            context={"request": request},
        )

        if serializer.is_valid():
            lab_order = serializer.save()
            return Response(
                {
                    "success": True,
                    "lab_order": LabOrderSerializer(lab_order).data,
                    "message": _("Lab order created successfully"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LabOrderItemResultView(APIView):
    """
    PATCH: Update lab order item result.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def patch(self, request, pk, item_pk):
        """Update lab order item result."""
        clinic = request.user.clinic

        lab_order = get_object_or_404(LabOrder, pk=pk, clinic=clinic)
        lab_order_item = get_object_or_404(LabOrderItem, pk=item_pk, lab_order=lab_order)

        serializer = LabOrderItemResultSerializer(
            lab_order_item,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            lab_order_item = serializer.save(result_date=timezone.now())
            return Response(
                {
                    "success": True,
                    "lab_order": LabOrderSerializer(lab_order).data,
                    "message": _("Lab order item result updated successfully"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
