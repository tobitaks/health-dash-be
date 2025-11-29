from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import CustomUser
from apps.users.serializers import (
    CustomUserSerializer,
    LoginSerializer,
    RegisterSerializer,
    UpdateProfileSerializer,
)


@method_decorator(csrf_exempt, name="dispatch")
class RegisterView(APIView):
    """
    Register a new user and create their clinic.

    POST /api/auth/register/
    {
        "email": "user@example.com",
        "password": "securepassword",
        "password_confirm": "securepassword",
        "clinic_name": "My Clinic"
    }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # Log the user in
            login(request, user, backend="allauth.account.auth_backends.AuthenticationBackend")

            return Response(
                {
                    "success": True,
                    "message": _("Registration successful."),
                    "user": CustomUserSerializer(user).data,
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


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    """
    Log in a user.

    POST /api/auth/login/
    {
        "email": "user@example.com",
        "password": "securepassword"
    }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]

            # Log the user in
            login(request, user, backend="allauth.account.auth_backends.AuthenticationBackend")

            return Response(
                {
                    "success": True,
                    "message": _("Login successful."),
                    "user": CustomUserSerializer(user).data,
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


class LogoutView(APIView):
    """
    Log out the current user.

    POST /api/auth/logout/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(
            {
                "success": True,
                "message": _("Logout successful."),
            },
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    """
    Get or update the current user's profile.

    GET /api/auth/me/
    PUT /api/auth/me/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user details."""
        return Response(
            {
                "success": True,
                "user": CustomUserSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        """Update current user profile."""
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": _("Profile updated successfully."),
                    "user": CustomUserSerializer(request.user).data,
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


class CheckAuthView(APIView):
    """
    Check if the user is authenticated.

    GET /api/auth/check/
    """

    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            return Response(
                {
                    "authenticated": True,
                    "user": CustomUserSerializer(request.user).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "authenticated": False,
                "user": None,
            },
            status=status.HTTP_200_OK,
        )
