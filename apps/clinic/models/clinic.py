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

    def create_default_roles(self):
        """Create default system roles for this clinic with associated policies."""
        from apps.users.models import Policy, Role, RolePolicy

        default_roles = [
            {
                "name": "Administrator",
                "slug": "administrator",
                "description": "Full access to all clinic features",
                "is_system": True,
                "is_admin": True,  # Full access flag
                "policy_codes": [],  # Admin doesn't need individual policies
                "color": "#dc2626",
                "icon": "Shield",
            },
            {
                "name": "Doctor",
                "slug": "doctor",
                "description": "Medical staff with patient care permissions",
                "is_system": True,
                "is_admin": False,
                "policy_codes": [
                    "patients.view",
                    "patients.create",
                    "patients.edit",
                    "consultations.view",
                    "consultations.create",
                    "consultations.edit",
                    "billing.view",
                ],
                "color": "#2563eb",
                "icon": "Stethoscope",
            },
            {
                "name": "Nurse",
                "slug": "nurse",
                "description": "Nursing staff with patient support permissions",
                "is_system": True,
                "is_admin": False,
                "policy_codes": [
                    "patients.view",
                    "patients.edit",
                    "consultations.view",
                ],
                "color": "#16a34a",
                "icon": "Heart",
            },
            {
                "name": "Secretary",
                "slug": "secretary",
                "description": "Front desk and administrative staff",
                "is_system": True,
                "is_admin": False,
                "policy_codes": [
                    "patients.view",
                    "patients.create",
                    "patients.edit",
                    "billing.view",
                    "billing.create",
                ],
                "color": "#9333ea",
                "icon": "ClipboardList",
            },
            {
                "name": "Cashier",
                "slug": "cashier",
                "description": "Billing and payment processing",
                "is_system": True,
                "is_admin": False,
                "policy_codes": [
                    "patients.view",
                    "billing.view",
                    "billing.create",
                    "billing.payments",
                ],
                "color": "#ea580c",
                "icon": "Wallet",
            },
        ]

        created_roles = []
        for role_data in default_roles:
            policy_codes = role_data.pop("policy_codes")

            role, created = Role.objects.get_or_create(
                clinic=self,
                slug=role_data["slug"],
                defaults={
                    "name": role_data["name"],
                    "description": role_data["description"],
                    "is_system": role_data["is_system"],
                    "is_admin": role_data["is_admin"],
                    "color": role_data["color"],
                    "icon": role_data["icon"],
                },
            )

            # Create RolePolicy entries for non-admin roles
            if created and not role_data["is_admin"]:
                for code in policy_codes:
                    try:
                        policy = Policy.objects.get(code=code)
                        RolePolicy.objects.get_or_create(role=role, policy=policy)
                    except Policy.DoesNotExist:
                        pass

            created_roles.append(role)

        return created_roles
