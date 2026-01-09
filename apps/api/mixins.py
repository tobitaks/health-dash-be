"""
Mixins for DRF views that provide common functionality.
"""

from django.shortcuts import get_object_or_404


class ClinicQuerySetMixin:
    """
    Mixin that automatically filters querysets by the user's clinic.

    This mixin should be used with DRF views that need to scope
    data to the current user's clinic. It provides:

    1. `get_queryset()` - Returns queryset filtered by user's clinic
    2. `get_clinic()` - Convenience method to get user's clinic
    3. `get_object_for_clinic()` - Get object ensuring it belongs to user's clinic

    Usage:
        class PatientListView(ClinicQuerySetMixin, APIView):
            queryset = Patient.objects.all()

            def get(self, request):
                patients = self.get_queryset()
                ...
    """

    queryset = None
    clinic_field = "clinic"  # Override if your model uses a different field name

    def get_clinic(self):
        """Get the current user's clinic."""
        return self.request.user.clinic

    def get_queryset(self):
        """
        Return queryset filtered by user's clinic.

        Override this method if you need custom filtering logic.
        """
        queryset = self.queryset
        if queryset is None:
            raise ValueError(f"{self.__class__.__name__} must define 'queryset' or override 'get_queryset()'")

        # Handle both QuerySet and Manager
        if hasattr(queryset, "all"):
            queryset = queryset.all()

        # Filter by clinic
        clinic = self.get_clinic()
        return queryset.filter(**{self.clinic_field: clinic})

    def get_object_for_clinic(self, model_class, pk, **extra_filters):
        """
        Get an object by pk, ensuring it belongs to the user's clinic.

        Args:
            model_class: The Django model class
            pk: Primary key of the object
            **extra_filters: Additional filter parameters

        Returns:
            Model instance

        Raises:
            Http404: If object not found or doesn't belong to user's clinic
        """
        clinic = self.get_clinic()
        return get_object_or_404(
            model_class,
            pk=pk,
            **{self.clinic_field: clinic},
            **extra_filters,
        )


class ClinicCreateMixin:
    """
    Mixin that automatically sets the clinic on object creation.

    Usage:
        class PatientCreateView(ClinicCreateMixin, APIView):
            def post(self, request):
                serializer = PatientSerializer(data=request.data)
                if serializer.is_valid():
                    patient = self.perform_create(serializer)
                    ...
    """

    clinic_field = "clinic"

    def get_clinic(self):
        """Get the current user's clinic."""
        return self.request.user.clinic

    def perform_create(self, serializer, **extra_kwargs):
        """
        Save the serializer with the user's clinic automatically set.

        Args:
            serializer: A valid DRF serializer instance
            **extra_kwargs: Additional fields to save

        Returns:
            The created model instance
        """
        clinic = self.get_clinic()
        return serializer.save(**{self.clinic_field: clinic}, **extra_kwargs)
