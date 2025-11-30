from django.db import models
from apps.utils.models import BaseModel


class Clinic(BaseModel):
    """
    Clinic model - represents a medical clinic/practice.
    One clinic can have multiple users (staff members).
    """

    name = models.CharField(max_length=200)

    # Contact Information
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    # Address
    address_street = models.CharField(max_length=255, blank=True, null=True)
    address_city = models.CharField(max_length=100, blank=True, null=True)
    address_region = models.CharField(max_length=100, blank=True, null=True)
    address_postal_code = models.CharField(max_length=20, blank=True, null=True)
    address_country = models.CharField(max_length=100, default="Philippines")

    # Business Hours (stored as JSON)
    business_hours = models.JSONField(default=dict, blank=True)

    # Branding
    logo = models.FileField(upload_to="clinic_logos/", blank=True, null=True)

    # Settings
    timezone = models.CharField(max_length=50, default="Asia/Manila")
    currency = models.CharField(max_length=3, default="PHP")

    # Status
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def full_address(self):
        """Returns formatted full address."""
        parts = [
            self.address_street,
            self.address_city,
            self.address_region,
            self.address_postal_code,
            self.address_country,
        ]
        return ", ".join(filter(None, parts))

    @property
    def owner(self):
        """Returns the clinic owner (user with isOwner=True)."""
        return self.users.filter(is_owner=True).first()

    @property
    def staff_count(self):
        """Returns the number of active staff members."""
        return self.users.filter(is_active=True).count()
