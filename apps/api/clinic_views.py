from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clinic.models import Clinic
from apps.clinic.serializers import ClinicSerializer


class CurrentClinicView(APIView):
    """
    Get or update the current user's clinic.

    GET /api/clinic/
    PUT /api/clinic/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user's clinic details."""
        clinic = request.user.clinic

        if not clinic:
            return Response(
                {
                    "success": False,
                    "error": "No clinic associated with this user.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "success": True,
                "clinic": ClinicSerializer(clinic).data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        """Update current user's clinic."""
        clinic = request.user.clinic

        if not clinic:
            return Response(
                {
                    "success": False,
                    "error": "No clinic associated with this user.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Only owners can update clinic details
        if not request.user.is_owner:
            return Response(
                {
                    "success": False,
                    "error": "Only clinic owners can update clinic details.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ClinicSerializer(clinic, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Clinic updated successfully.",
                    "clinic": serializer.data,
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
