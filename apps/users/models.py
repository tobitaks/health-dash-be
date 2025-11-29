import hashlib
import uuid
from functools import cached_property

from allauth.account.models import EmailAddress
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.subscriptions.models import SubscriptionModelBase
from apps.users.helpers import validate_profile_picture


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
