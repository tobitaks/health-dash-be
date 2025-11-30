"""
API views for Service CRUD operations.
"""

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clinic.models import Service
from apps.clinic.serializers import ServiceCreateUpdateSerializer, ServiceSerializer


class ServiceListCreateView(APIView):
    """
    GET: List all services for the clinic.
    POST: Create a new service.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all services for the clinic."""
        clinic = request.user.clinic
        if not clinic:
            return Response(
                {"success": False, "message": _("User has no clinic")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        services = Service.objects.filter(clinic=clinic)
        return Response(
            {
                "success": True,
                "services": ServiceSerializer(services, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new service."""
        clinic = request.user.clinic
        if not clinic:
            return Response(
                {"success": False, "message": _("User has no clinic")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ServiceCreateUpdateSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            service = serializer.save(clinic=clinic)
            return Response(
                {
                    "success": True,
                    "service": ServiceSerializer(service).data,
                    "message": _("Service created successfully"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ServiceDetailView(APIView):
    """
    GET: Get service details.
    PUT: Update a service.
    DELETE: Delete a service.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        """Get service by ID, ensuring it belongs to user's clinic."""
        return get_object_or_404(Service, pk=pk, clinic=request.user.clinic)

    def get(self, request, pk):
        """Get service details."""
        service = self.get_object(pk, request)
        return Response(
            {
                "success": True,
                "service": ServiceSerializer(service).data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        """Update a service."""
        service = self.get_object(pk, request)

        serializer = ServiceCreateUpdateSerializer(
            service,
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            service = serializer.save()
            return Response(
                {
                    "success": True,
                    "service": ServiceSerializer(service).data,
                    "message": _("Service updated successfully"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        """Delete a service."""
        service = self.get_object(pk, request)
        service.delete()

        return Response(
            {
                "success": True,
                "message": _("Service deleted successfully"),
            },
            status=status.HTTP_200_OK,
        )
