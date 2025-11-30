from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.clinic.models import Clinic
from apps.clinic.serializers import ClinicSerializer

from .models import CustomUser, Policy, Role, RolePolicy, UserRole


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Basic serializer to pass CustomUser details to the front end.
    Extend with any fields your app needs.
    """

    clinic = ClinicSerializer(read_only=True)
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

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
            "roles",
            "permissions",
        )

    def get_roles(self, obj):
        """Return list of role objects assigned to user."""
        from apps.users.serializers import RoleSerializer

        user_roles = obj.user_roles.select_related("role")
        return [
            {
                "id": ur.role.id,
                "name": ur.role.name,
                "slug": ur.role.slug,
                "color": ur.role.color,
                "icon": ur.role.icon,
            }
            for ur in user_roles
        ]

    def get_permissions(self, obj):
        """Return list of permission codes for user."""
        return list(obj.get_permissions())


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

        # Create default roles for the clinic
        roles = clinic.create_default_roles()

        # Create user (owner is always a doctor)
        user = CustomUser.objects.create_user(
            username=validated_data["email"],  # Use email as username
            email=validated_data["email"],
            password=validated_data["password"],
            clinic=clinic,
            role=CustomUser.Role.DOCTOR,
            is_owner=True,
        )

        # Assign Administrator role to the owner
        admin_role = next((r for r in roles if r.slug == "administrator"), None)
        if admin_role:
            UserRole.objects.create(user=user, role=admin_role)

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


class StaffListSerializer(serializers.ModelSerializer):
    """Serializer for listing staff members."""

    roles = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_owner",
            "is_active",
            "date_joined",
            "roles",
        )
        read_only_fields = fields

    def get_roles(self, obj):
        """Return list of role objects assigned to user."""
        user_roles = obj.user_roles.select_related("role")
        return [
            {
                "id": ur.role.id,
                "name": ur.role.name,
                "slug": ur.role.slug,
                "color": ur.role.color,
                "icon": ur.role.icon,
            }
            for ur in user_roles
        ]


class StaffCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new staff member with password."""

    password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "password",
            "first_name",
            "last_name",
        )

    def validate_email(self, value):
        """Check that email is unique within the clinic."""
        clinic = self.context["request"].user.clinic
        if CustomUser.objects.filter(email=value, clinic=clinic).exists():
            raise serializers.ValidationError(_("A staff member with this email already exists."))
        return value.lower()

    def create(self, validated_data):
        """Create staff user."""
        clinic = self.context["request"].user.clinic
        password = validated_data.pop("password")

        # Default role is Secretary - can be changed via Roles page
        user = CustomUser.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=password,
            clinic=clinic,
            is_owner=False,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=CustomUser.Role.SECRETARY,
        )

        return user


class StaffUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating staff member (with optional password reset)."""

    password = serializers.CharField(write_only=True, required=False, min_length=6, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "password",
            "first_name",
            "last_name",
            "is_active",
        )

    def validate_email(self, value):
        """Check that email is unique within the clinic (excluding self)."""
        clinic = self.context["request"].user.clinic
        instance = self.instance
        if CustomUser.objects.filter(email=value, clinic=clinic).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError(_("A staff member with this email already exists."))
        return value.lower()

    def update(self, instance, validated_data):
        """Update staff user, optionally resetting password."""
        password = validated_data.pop("password", None)

        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update username if email changed
        if "email" in validated_data:
            instance.username = validated_data["email"]

        # Reset password if provided
        if password:
            instance.set_password(password)

        instance.save()
        return instance


class PolicySerializer(serializers.ModelSerializer):
    """Serializer for listing policies."""

    class Meta:
        model = Policy
        fields = ("id", "code", "name", "category")


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for listing roles with user count and policies."""

    user_count = serializers.SerializerMethodField()
    policies = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "is_system",
            "is_admin",
            "policies",
            "color",
            "icon",
            "user_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_user_count(self, obj):
        return obj.user_roles.count()

    def get_policies(self, obj):
        """Return list of policies for this role."""
        policies = obj.get_policies()
        return PolicySerializer(policies, many=True).data


class RoleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating roles."""

    policy_ids = serializers.PrimaryKeyRelatedField(
        queryset=Policy.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = Role
        fields = (
            "name",
            "slug",
            "description",
            "is_admin",
            "policy_ids",
            "color",
            "icon",
        )

    def validate_slug(self, value):
        """Ensure slug is unique within the clinic."""
        clinic = self.context["request"].user.clinic
        instance = self.instance

        queryset = Role.objects.filter(clinic=clinic, slug=value)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(_("A role with this slug already exists in your clinic."))
        return value

    def create(self, validated_data):
        """Create role with clinic from request user."""
        clinic = self.context["request"].user.clinic
        policy_ids = validated_data.pop("policy_ids", [])

        role = Role.objects.create(clinic=clinic, **validated_data)

        # Create RolePolicy entries
        for policy in policy_ids:
            RolePolicy.objects.create(role=role, policy=policy)

        return role

    def update(self, instance, validated_data):
        """Update role and its policies."""
        policy_ids = validated_data.pop("policy_ids", None)

        # Update role fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update policies if provided
        if policy_ids is not None:
            # Clear existing policies
            instance.role_policies.all().delete()
            # Add new policies
            for policy in policy_ids:
                RolePolicy.objects.create(role=instance, policy=policy)

        return instance


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for user role assignments."""

    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        write_only=True,
        source="role",
    )

    class Meta:
        model = UserRole
        fields = ("id", "role", "role_id", "assigned_by", "created_at")
        read_only_fields = ("id", "assigned_by", "created_at")

    def validate_role_id(self, value):
        """Ensure role belongs to the same clinic as the user."""
        request = self.context.get("request")
        if request and value.clinic != request.user.clinic:
            raise serializers.ValidationError(_("Role must belong to your clinic."))
        return value

    def create(self, validated_data):
        """Create user role assignment."""
        request = self.context.get("request")
        validated_data["assigned_by"] = request.user if request else None
        return super().create(validated_data)


class UserWithRolesSerializer(serializers.ModelSerializer):
    """Serializer for user with their assigned roles."""

    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "is_owner",
            "is_active",
            "roles",
            "permissions",
        )

    def get_roles(self, obj):
        user_roles = obj.user_roles.select_related("role")
        return RoleSerializer([ur.role for ur in user_roles], many=True).data

    def get_permissions(self, obj):
        return list(obj.get_permissions())
