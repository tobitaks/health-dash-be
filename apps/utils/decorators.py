"""
Common decorators for views.
"""

from functools import wraps

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response


def require_clinic(view_func):
    """
    Decorator for function-based views that require a clinic.

    Returns a 400 Bad Request response if the user has no clinic.
    This decorator should be used after authentication decorators.

    Usage:
        @api_view(['GET'])
        @permission_classes([IsAuthenticated])
        @require_clinic
        def my_view(request):
            clinic = request.user.clinic  # Guaranteed to exist
            ...

    Note: For class-based views, use the `HasClinicAccess` permission
    class from `apps.api.permissions` instead.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, "user") or not request.user.is_authenticated:
            # Let authentication handle this case
            return view_func(request, *args, **kwargs)

        if not hasattr(request.user, "clinic") or request.user.clinic is None:
            return Response(
                {"success": False, "message": _("User has no clinic")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def require_owner(view_func):
    """
    Decorator for function-based views that require the user to be a clinic owner.

    Returns a 403 Forbidden response if the user is not the clinic owner.
    This decorator should be used after @require_clinic.

    Usage:
        @api_view(['POST'])
        @permission_classes([IsAuthenticated])
        @require_clinic
        @require_owner
        def create_staff(request):
            # Only clinic owners can reach here
            ...
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, "user") or not request.user.is_authenticated:
            # Let authentication handle this case
            return view_func(request, *args, **kwargs)

        if not getattr(request.user, "is_owner", False):
            return Response(
                {"success": False, "message": _("Only the clinic owner can perform this action.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        return view_func(request, *args, **kwargs)

    return wrapper
