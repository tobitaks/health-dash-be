"""
API views for Medicine CRUD operations.
"""

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.medicines.models import Medicine
from apps.medicines.serializers import MedicineSerializer


class MedicineListCreateView(APIView):
    """
    GET: List all medicines for the clinic.
    POST: Create a new medicine.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all medicines for the clinic."""
        clinic = request.user.clinic
        if not clinic:
            return Response(
                {"success": False, "message": _("User has no clinic")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filter options
        is_active = request.query_params.get("is_active")
        category = request.query_params.get("category")
        form = request.query_params.get("form")
        search = request.query_params.get("search")

        medicines = Medicine.objects.filter(clinic=clinic)

        # Apply filters
        if is_active is not None:
            is_active_bool = is_active.lower() in ("true", "1", "yes")
            medicines = medicines.filter(is_active=is_active_bool)

        if category:
            medicines = medicines.filter(category=category)

        if form:
            medicines = medicines.filter(form=form)

        if search:
            medicines = medicines.filter(generic_name__icontains=search) | medicines.filter(
                brand_name__icontains=search
            )

        return Response(
            {
                "success": True,
                "medicines": MedicineSerializer(medicines, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new medicine."""
        clinic = request.user.clinic
        if not clinic:
            return Response(
                {"success": False, "message": _("User has no clinic")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MedicineSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            medicine = serializer.save(clinic=clinic)
            return Response(
                {
                    "success": True,
                    "medicine": MedicineSerializer(medicine).data,
                    "message": _("Medicine created successfully"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class MedicineDetailView(APIView):
    """
    GET: Get medicine details.
    PUT: Update a medicine.
    DELETE: Delete a medicine.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        """Get medicine by ID, ensuring it belongs to user's clinic."""
        return get_object_or_404(Medicine, pk=pk, clinic=request.user.clinic)

    def get(self, request, pk):
        """Get medicine details."""
        medicine = self.get_object(pk, request)
        return Response(
            {
                "success": True,
                "medicine": MedicineSerializer(medicine).data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        """Update a medicine."""
        medicine = self.get_object(pk, request)

        serializer = MedicineSerializer(
            medicine,
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            medicine = serializer.save()
            return Response(
                {
                    "success": True,
                    "medicine": MedicineSerializer(medicine).data,
                    "message": _("Medicine updated successfully"),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        """Delete a medicine."""
        medicine = self.get_object(pk, request)
        medicine.delete()

        return Response(
            {
                "success": True,
                "message": _("Medicine deleted successfully"),
            },
            status=status.HTTP_200_OK,
        )


class MedicineOptionsView(APIView):
    """
    GET: Get form and category options for dropdowns.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get form and category options."""
        return Response(
            {
                "success": True,
                "forms": [{"value": value, "label": str(label)} for value, label in Medicine.FORM_CHOICES],
                "categories": [{"value": value, "label": str(label)} for value, label in Medicine.CATEGORY_CHOICES],
            },
            status=status.HTTP_200_OK,
        )
