import typing

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework_api_key.permissions import BaseHasAPIKey

from .helpers import get_user_from_request
from .models import UserAPIKey


class HasClinicAccess(BasePermission):
    """
    Permission class that checks if the user has an associated clinic.

    This centralizes the clinic tenancy check that was previously duplicated
    across all views. Returns a 403 Forbidden response if the user has no clinic.
    """

    message = _("User has no clinic")

    def has_permission(self, request: HttpRequest, view: typing.Any) -> bool:
        # Allow unauthenticated requests to pass through
        # (they will be caught by authentication classes)
        if not request.user or not request.user.is_authenticated:
            return True

        # Check if user has an associated clinic
        return hasattr(request.user, "clinic") and request.user.clinic is not None


class HasUserAPIKey(BaseHasAPIKey):
    model = UserAPIKey

    def has_permission(self, request: HttpRequest, view: typing.Any) -> bool:
        has_perm = super().has_permission(request, view)
        if has_perm:
            # if they have permission, also populate the request.user object for convenience
            request.user = get_user_from_request(request)

            if request.user and not request.user.is_active:
                has_perm = False

        return has_perm


# hybrid permission class that can check for API keys or authentication
IsAuthenticatedOrHasUserAPIKey = IsAuthenticated | HasUserAPIKey

# Combined permission class that requires authentication AND clinic access
# This is the recommended permission class for clinic-scoped endpoints
IsAuthenticatedWithClinicAccess = (IsAuthenticated | HasUserAPIKey) & HasClinicAccess
