"""
Role management API views.
"""

from collections import defaultdict

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsAuthenticatedWithClinicAccess
from apps.users.models import CustomUser, Policy, Role, RolePolicy, UserRole
from apps.users.serializers import (
    PolicySerializer,
    RoleCreateUpdateSerializer,
    RoleSerializer,
    UserRoleSerializer,
)


class RoleListCreateView(APIView):
    """
    GET: List all roles for the clinic.
    POST: Create a new role.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get(self, request):
        """List all roles for the clinic."""
        clinic = request.user.clinic

        roles = Role.objects.filter(clinic=clinic)
        serializer = RoleSerializer(roles, many=True)

        return Response(
            {
                "success": True,
                "roles": serializer.data,
            }
        )

    def post(self, request):
        """Create a new role (owner only)."""
        if not request.user.is_owner:
            return Response(
                {"success": False, "message": _("Only clinic owners can create roles")},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = RoleCreateUpdateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            role = serializer.save()
            return Response(
                {
                    "success": True,
                    "role": RoleSerializer(role).data,
                    "message": _("Role created successfully"),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RoleDetailView(APIView):
    """
    GET: Get role details.
    PUT: Update a role.
    DELETE: Delete a role (non-system only).
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get_object(self, pk, request):
        """Get role by ID, ensuring it belongs to user's clinic."""
        return get_object_or_404(Role, pk=pk, clinic=request.user.clinic)

    def get(self, request, pk):
        """Get role details."""
        role = self.get_object(pk, request)
        return Response(
            {
                "success": True,
                "role": RoleSerializer(role).data,
            }
        )

    def put(self, request, pk):
        """Update a role (owner only)."""
        if not request.user.is_owner:
            return Response(
                {"success": False, "message": _("Only clinic owners can update roles")},
                status=status.HTTP_403_FORBIDDEN,
            )

        role = self.get_object(pk, request)

        # System roles can only have policies updated (not name, slug, etc.)
        if role.is_system:
            allowed_fields = {"policy_ids", "is_admin"}
            filtered_data = {k: v for k, v in request.data.items() if k in allowed_fields}
            if not filtered_data:
                return Response(
                    {"success": False, "message": _("System roles can only have policies updated")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Update is_admin if provided
            if "is_admin" in filtered_data:
                role.is_admin = filtered_data["is_admin"]
                role.save()

            # Update policies if provided
            if "policy_ids" in filtered_data:
                # Clear existing policies
                role.role_policies.all().delete()
                # Add new policies
                for policy_id in filtered_data["policy_ids"]:
                    try:
                        policy = Policy.objects.get(pk=policy_id)
                        RolePolicy.objects.create(role=role, policy=policy)
                    except Policy.DoesNotExist:
                        pass

            return Response(
                {
                    "success": True,
                    "role": RoleSerializer(role).data,
                    "message": _("Role updated successfully"),
                }
            )

        serializer = RoleCreateUpdateSerializer(role, data=request.data, context={"request": request}, partial=True)
        if serializer.is_valid():
            role = serializer.save()
            return Response(
                {
                    "success": True,
                    "role": RoleSerializer(role).data,
                    "message": _("Role updated successfully"),
                }
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        """Delete a role (owner only, non-system roles)."""
        if not request.user.is_owner:
            return Response(
                {"success": False, "message": _("Only clinic owners can delete roles")},
                status=status.HTTP_403_FORBIDDEN,
            )

        role = self.get_object(pk, request)

        if role.is_system:
            return Response(
                {"success": False, "message": _("System roles cannot be deleted")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        role.delete()
        return Response(
            {
                "success": True,
                "message": _("Role deleted successfully"),
            }
        )


class PolicyListView(APIView):
    """
    GET: List all available policies grouped by category.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get(self, request):
        """Return all available policies grouped by category."""
        policies = Policy.objects.all().order_by("category", "name")

        # Group by category
        grouped = defaultdict(list)
        for policy in policies:
            grouped[policy.category].append(PolicySerializer(policy).data)

        # Convert to list format for frontend
        result = [{"category": category, "policies": policies_list} for category, policies_list in grouped.items()]

        return Response(
            {
                "success": True,
                "policies": result,
            }
        )


class UserRoleListView(APIView):
    """
    GET: List roles assigned to a user.
    POST: Assign a role to a user.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def get_user(self, pk, request):
        """Get user by ID, ensuring they belong to the same clinic."""
        return get_object_or_404(CustomUser, pk=pk, clinic=request.user.clinic)

    def get(self, request, user_id):
        """List roles assigned to a user."""
        user = self.get_user(user_id, request)
        user_roles = UserRole.objects.filter(user=user).select_related("role")
        serializer = UserRoleSerializer(user_roles, many=True)

        return Response(
            {
                "success": True,
                "user_roles": serializer.data,
            }
        )

    def post(self, request, user_id):
        """Assign a role to a user (owner only)."""
        if not request.user.is_owner:
            return Response(
                {"success": False, "message": _("Only clinic owners can assign roles")},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_user(user_id, request)

        # Validate role_id
        role_id = request.data.get("role_id")
        if not role_id:
            return Response(
                {"success": False, "message": _("role_id is required")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        role = get_object_or_404(Role, pk=role_id, clinic=request.user.clinic)

        # Check if already assigned
        if UserRole.objects.filter(user=user, role=role).exists():
            return Response(
                {"success": False, "message": _("User already has this role")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_role = UserRole.objects.create(user=user, role=role, assigned_by=request.user)
        serializer = UserRoleSerializer(user_role)

        return Response(
            {
                "success": True,
                "user_role": serializer.data,
                "message": _("Role assigned successfully"),
            },
            status=status.HTTP_201_CREATED,
        )


class UserRoleDetailView(APIView):
    """
    DELETE: Remove a role from a user.
    """

    permission_classes = [IsAuthenticatedWithClinicAccess]

    def delete(self, request, user_id, role_id):
        """Remove a role from a user (owner only)."""
        if not request.user.is_owner:
            return Response(
                {"success": False, "message": _("Only clinic owners can remove roles")},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = get_object_or_404(CustomUser, pk=user_id, clinic=request.user.clinic)
        role = get_object_or_404(Role, pk=role_id, clinic=request.user.clinic)

        user_role = get_object_or_404(UserRole, user=user, role=role)
        user_role.delete()

        return Response(
            {
                "success": True,
                "message": _("Role removed successfully"),
            }
        )
