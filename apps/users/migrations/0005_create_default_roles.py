"""
Data migration to create default roles for existing clinics
and migrate existing user.role CharField to UserRole entries.
"""

from django.db import migrations
from django.utils.text import slugify


# Default roles with their permissions
DEFAULT_ROLES = [
    {
        "name": "Administrator",
        "slug": "administrator",
        "description": "Full access to all clinic features",
        "is_system": True,
        "permissions": ["*"],
        "color": "#dc2626",
        "icon": "Shield",
    },
    {
        "name": "Doctor",
        "slug": "doctor",
        "description": "Medical staff with patient care permissions",
        "is_system": True,
        "permissions": [
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
        "permissions": [
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
        "permissions": [
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
        "permissions": [
            "patients.view",
            "billing.view",
            "billing.create",
            "billing.payments",
        ],
        "color": "#ea580c",
        "icon": "Wallet",
    },
]

# Map old role CharField values to new role slugs
ROLE_MAPPING = {
    "Admin": "administrator",
    "Doctor": "doctor",
    "Nurse": "nurse",
    "Secretary": "secretary",
    "Cashier": "cashier",
}


def create_default_roles(apps, schema_editor):
    """Create default roles for each existing clinic."""
    Clinic = apps.get_model("clinic", "Clinic")
    Role = apps.get_model("users", "Role")

    for clinic in Clinic.objects.all():
        for role_data in DEFAULT_ROLES:
            Role.objects.get_or_create(
                clinic=clinic,
                slug=role_data["slug"],
                defaults={
                    "name": role_data["name"],
                    "description": role_data["description"],
                    "is_system": role_data["is_system"],
                    "permissions": role_data["permissions"],
                    "color": role_data["color"],
                    "icon": role_data["icon"],
                },
            )


def migrate_user_roles(apps, schema_editor):
    """Migrate existing user.role CharField to UserRole entries."""
    CustomUser = apps.get_model("users", "CustomUser")
    Role = apps.get_model("users", "Role")
    UserRole = apps.get_model("users", "UserRole")

    for user in CustomUser.objects.filter(clinic__isnull=False):
        old_role = user.role
        if old_role and old_role in ROLE_MAPPING:
            new_role_slug = ROLE_MAPPING[old_role]
            try:
                role = Role.objects.get(clinic=user.clinic, slug=new_role_slug)
                UserRole.objects.get_or_create(
                    user=user,
                    role=role,
                    defaults={"assigned_by": None},
                )
            except Role.DoesNotExist:
                pass


def forward(apps, schema_editor):
    """Run both migrations in order."""
    create_default_roles(apps, schema_editor)
    migrate_user_roles(apps, schema_editor)


def reverse(apps, schema_editor):
    """Reverse the migration - delete all UserRole entries and non-custom roles."""
    UserRole = apps.get_model("users", "UserRole")
    Role = apps.get_model("users", "Role")

    # Delete all UserRole entries
    UserRole.objects.all().delete()

    # Delete only system roles (user-created roles should remain)
    Role.objects.filter(is_system=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_role_userrole"),
        ("clinic", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
