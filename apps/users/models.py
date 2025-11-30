import hashlib
import uuid
from functools import cached_property

from allauth.account.models import EmailAddress
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.subscriptions.models import SubscriptionModelBase
from apps.users.helpers import validate_profile_picture
from apps.utils.models import BaseModel


def _get_avatar_filename(instance, filename):
    """Use random filename prevent overwriting existing files & to fix caching issues."""
    return f"profile-pictures/{uuid.uuid4()}.{filename.split('.')[-1]}"


class CustomUser(SubscriptionModelBase, AbstractUser):
    """
    Add additional fields to the user model here.
    """

    class Role(models.TextChoices):
        ADMIN = "Admin", _("Admin")
        DOCTOR = "Doctor", _("Doctor")
        NURSE = "Nurse", _("Nurse")
        SECRETARY = "Secretary", _("Secretary")
        CASHIER = "Cashier", _("Cashier")

    avatar = models.FileField(upload_to=_get_avatar_filename, blank=True, validators=[validate_profile_picture])
    language = models.CharField(max_length=10, blank=True, null=True)
    timezone = models.CharField(max_length=100, blank=True, default="")

    # Clinic relationship
    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
        help_text=_("The clinic this user belongs to"),
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN,
        help_text=_("User's role in the clinic"),
    )
    is_owner = models.BooleanField(
        default=False,
        help_text=_("Whether this user is the clinic owner"),
    )

    def __str__(self):
        return f"{self.get_full_name()} <{self.email or self.username}>"

    def get_display_name(self) -> str:
        if self.get_full_name().strip():
            return self.get_full_name()
        return self.email or self.username

    @property
    def avatar_url(self) -> str:
        if self.avatar:
            return self.avatar.url
        else:
            return f"https://www.gravatar.com/avatar/{self.gravatar_id}?s=128&d=identicon"

    @property
    def gravatar_id(self) -> str:
        # https://en.gravatar.com/site/implement/hash/
        return hashlib.md5(self.email.lower().strip().encode("utf-8")).hexdigest()

    @cached_property
    def has_verified_email(self):
        return EmailAddress.objects.filter(user=self, verified=True).exists()

    def get_roles(self):
        """Returns all roles assigned to this user."""
        from apps.users.models import Role

        return Role.objects.filter(user_roles__user=self)

    def get_permissions(self):
        """Returns all permission codes from user's roles."""
        permissions = set()
        for role in self.get_roles():
            if role.is_admin:
                return {"*"}
            permissions.update(role.get_policy_codes())
        return permissions

    def has_permission(self, code):
        """Check if user has a specific permission."""
        permissions = self.get_permissions()
        if "*" in permissions:
            return True
        return code in permissions


class Policy(BaseModel):
    """
    Global permission policy - system-wide, not per-clinic.
    Defines individual permissions that can be attached to roles.
    """

    code = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("Permission code (e.g., 'patients.view')"),
    )
    name = models.CharField(
        max_length=100,
        help_text=_("Display name (e.g., 'View Patients')"),
    )
    category = models.CharField(
        max_length=50,
        help_text=_("Category for grouping (e.g., 'Patients', 'Billing')"),
    )

    class Meta:
        ordering = ["category", "name"]
        verbose_name_plural = "Policies"

    def __str__(self):
        return f"{self.category}: {self.name}"


class Role(BaseModel):
    """
    Custom role model for per-clinic role management.
    Each clinic can have its own roles with customizable policies.
    """

    name = models.CharField(max_length=100, help_text=_("Display name of the role"))
    slug = models.SlugField(max_length=100, help_text=_("URL-safe identifier"))
    description = models.TextField(blank=True, help_text=_("Description of the role's responsibilities"))
    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.CASCADE,
        related_name="roles",
        help_text=_("The clinic this role belongs to"),
    )
    is_system = models.BooleanField(
        default=False,
        help_text=_("System roles cannot be deleted"),
    )
    is_admin = models.BooleanField(
        default=False,
        help_text=_("Admin roles have full access to all features"),
    )
    # DEPRECATED: Will be removed after migration to Policy model
    permissions = models.JSONField(
        default=list,
        help_text=_("DEPRECATED - Use RolePolicy instead"),
    )
    color = models.CharField(
        max_length=20,
        default="#6b7280",
        help_text=_("Color for UI display (hex code)"),
    )
    icon = models.CharField(
        max_length=50,
        default="User",
        help_text=_("Icon name for UI display"),
    )

    class Meta:
        unique_together = ["clinic", "slug"]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.clinic.name})"

    def get_policies(self):
        """Returns all policies for this role."""
        return Policy.objects.filter(role_policies__role=self)

    def get_policy_codes(self):
        """Returns list of policy codes for this role."""
        if self.is_admin:
            return ["*"]
        return list(self.get_policies().values_list("code", flat=True))


class RolePolicy(BaseModel):
    """
    Junction table for Role-Policy many-to-many relationship.
    Allows roles to have multiple policies attached.
    """

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_policies",
        help_text=_("The role this policy is attached to"),
    )
    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        related_name="role_policies",
        help_text=_("The policy attached to the role"),
    )

    class Meta:
        unique_together = ["role", "policy"]

    def __str__(self):
        return f"{self.role.name} - {self.policy.code}"


class UserRole(BaseModel):
    """
    Junction table for assigning roles to users.
    A user can have multiple roles within their clinic.
    """

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="user_roles",
        help_text=_("The user assigned to this role"),
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles",
        help_text=_("The role assigned to the user"),
    )
    assigned_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="role_assignments",
        help_text=_("The user who assigned this role"),
    )

    class Meta:
        unique_together = ["user", "role"]

    def __str__(self):
        return f"{self.user.email} - {self.role.name}"
