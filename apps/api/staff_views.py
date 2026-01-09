from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsAuthenticatedWithClinicAccess
from apps.users.models import CustomUser
from apps.users.serializers import (
    StaffCreateSerializer,
    StaffListSerializer,
    StaffUpdateSerializer,
)


class StaffListCreateView(APIView):
    """
    List all staff in the clinic or create a new staff member.

    GET /api/staff/ - List all staff
    POST /api/staff/ - Create new staff member
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get(self, request):
        """List all staff members in the same clinic."""
        clinic = request.user.clinic
        staff = CustomUser.objects.filter(clinic=clinic).order_by("-date_joined")
        serializer = StaffListSerializer(staff, many=True)

        return Response(
            {
                "success": True,
                "staff": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new staff member."""
        # Only owner can create staff
        if not request.user.is_owner:
            return Response(
                {"success": False, "message": _("Only the clinic owner can create staff members.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = StaffCreateSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": _("Staff member created successfully."),
                    "staff": StaffListSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class StaffDetailView(APIView):
    """
    Retrieve, update, or delete a staff member.

    GET /api/staff/<id>/ - Get staff details
    PUT /api/staff/<id>/ - Update staff member
    DELETE /api/staff/<id>/ - Deactivate staff member
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get_object(self, pk, request):
        """Get staff member, ensuring they belong to the same clinic."""
        return get_object_or_404(CustomUser, pk=pk, clinic=request.user.clinic)

    def get(self, request, pk):
        """Get staff member details."""
        staff = self.get_object(pk, request)
        serializer = StaffListSerializer(staff)

        return Response(
            {
                "success": True,
                "staff": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        """Update a staff member."""
        # Only owner can update staff
        if not request.user.is_owner:
            return Response(
                {"success": False, "message": _("Only the clinic owner can update staff members.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        staff = self.get_object(pk, request)

        # Cannot update the owner's account via this endpoint
        if staff.is_owner:
            return Response(
                {"success": False, "message": _("Cannot modify the clinic owner via this endpoint.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = StaffUpdateSerializer(staff, data=request.data, context={"request": request}, partial=True)

        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": _("Staff member updated successfully."),
                    "staff": StaffListSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        """Deactivate a staff member (soft delete)."""
        # Only owner can delete staff
        if not request.user.is_owner:
            return Response(
                {"success": False, "message": _("Only the clinic owner can deactivate staff members.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        staff = self.get_object(pk, request)

        # Cannot delete the owner
        if staff.is_owner:
            return Response(
                {"success": False, "message": _("Cannot deactivate the clinic owner.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Soft delete - set is_active to False
        staff.is_active = False
        staff.save()

        return Response(
            {
                "success": True,
                "message": _("Staff member deactivated successfully."),
            },
            status=status.HTTP_200_OK,
        )
