from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.clinic.models import Clinic
from apps.clinic.serializers import ClinicSerializer

from .models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Basic serializer to pass CustomUser details to the front end.
    Extend with any fields your app needs.
    """

    clinic = ClinicSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar_url",
            "get_display_name",
            "clinic",
            "role",
            "is_owner",
        )


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration with clinic creation."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    clinic_name = serializers.CharField(required=True, max_length=200)

    def validate_email(self, value):
        """Check that email is unique."""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("A user with this email already exists."))
        return value.lower()

    def validate(self, attrs):
        """Check that passwords match."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": _("Passwords do not match.")})
        return attrs

    def create(self, validated_data):
        """Create user and clinic."""
        # Remove password_confirm as it's not needed for user creation
        validated_data.pop("password_confirm")
        clinic_name = validated_data.pop("clinic_name")

        # Create clinic first
        clinic = Clinic.objects.create(name=clinic_name)

        # Create user (owner is always a doctor)
        user = CustomUser.objects.create_user(
            username=validated_data["email"],  # Use email as username
            email=validated_data["email"],
            password=validated_data["password"],
            clinic=clinic,
            role=CustomUser.Role.DOCTOR,
            is_owner=True,
        )

        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        """Validate and authenticate user."""
        email = attrs.get("email", "").lower()
        password = attrs.get("password")

        if email and password:
            # Authenticate using email as username
            user = authenticate(username=email, password=password)

            if not user:
                raise serializers.ValidationError(_("Invalid email or password."))

            if not user.is_active:
                raise serializers.ValidationError(_("This account has been deactivated."))

            attrs["user"] = user
        else:
            raise serializers.ValidationError(_("Email and password are required."))

        return attrs


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "avatar", "language", "timezone")
