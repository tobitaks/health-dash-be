"""
Data migration to:
1. Seed default policies
2. Migrate existing role permissions JSON to RolePolicy entries
3. Set is_admin for roles with '*' permission
"""

from django.db import migrations


# Default policies to seed
DEFAULT_POLICIES = [
    # Patients
    {"code": "patients.view", "name": "View Patients", "category": "Patients"},
    {"code": "patients.create", "name": "Create Patients", "category": "Patients"},
    {"code": "patients.edit", "name": "Edit Patients", "category": "Patients"},
    {"code": "patients.delete", "name": "Delete Patients", "category": "Patients"},
    # Consultations
    {"code": "consultations.view", "name": "View Consultations", "category": "Consultations"},
    {"code": "consultations.create", "name": "Create Consultations", "category": "Consultations"},
    {"code": "consultations.edit", "name": "Edit Consultations", "category": "Consultations"},
    {"code": "consultations.delete", "name": "Delete Consultations", "category": "Consultations"},
    # Billing
    {"code": "billing.view", "name": "View Billing", "category": "Billing"},
    {"code": "billing.create", "name": "Create Invoices", "category": "Billing"},
    {"code": "billing.edit", "name": "Edit Invoices", "category": "Billing"},
    {"code": "billing.payments", "name": "Process Payments", "category": "Billing"},
    # Staff
    {"code": "staff.view", "name": "View Staff", "category": "Staff"},
    {"code": "staff.create", "name": "Create Staff", "category": "Staff"},
    {"code": "staff.edit", "name": "Edit Staff", "category": "Staff"},
    {"code": "staff.delete", "name": "Delete Staff", "category": "Staff"},
    # Roles
    {"code": "roles.view", "name": "View Roles", "category": "Roles"},
    {"code": "roles.create", "name": "Create Roles", "category": "Roles"},
    {"code": "roles.edit", "name": "Edit Roles", "category": "Roles"},
    {"code": "roles.delete", "name": "Delete Roles", "category": "Roles"},
    # Settings
    {"code": "settings.view", "name": "View Settings", "category": "Settings"},
    {"code": "settings.edit", "name": "Edit Settings", "category": "Settings"},
]


def seed_policies(apps, schema_editor):
    """Create all default policies."""
    Policy = apps.get_model("users", "Policy")

    for policy_data in DEFAULT_POLICIES:
        Policy.objects.get_or_create(
            code=policy_data["code"],
            defaults={
                "name": policy_data["name"],
                "category": policy_data["category"],
            },
        )


def migrate_role_permissions(apps, schema_editor):
    """
    Migrate existing role.permissions JSON to RolePolicy entries.
    Also set is_admin=True for roles with '*' permission.
    """
    Role = apps.get_model("users", "Role")
    Policy = apps.get_model("users", "Policy")
    RolePolicy = apps.get_model("users", "RolePolicy")

    for role in Role.objects.all():
        permissions = role.permissions or []

        # Check for admin permission
        if "*" in permissions:
            role.is_admin = True
            role.save()
            continue

        # Create RolePolicy entries for each permission code
        for code in permissions:
            try:
                policy = Policy.objects.get(code=code)
                RolePolicy.objects.get_or_create(role=role, policy=policy)
            except Policy.DoesNotExist:
                # Skip unknown permission codes
                pass


def forward(apps, schema_editor):
    """Run both migrations in order."""
    seed_policies(apps, schema_editor)
    migrate_role_permissions(apps, schema_editor)


def reverse(apps, schema_editor):
    """Reverse the migration."""
    RolePolicy = apps.get_model("users", "RolePolicy")
    Policy = apps.get_model("users", "Policy")
    Role = apps.get_model("users", "Role")

    # Clear RolePolicy entries
    RolePolicy.objects.all().delete()

    # Clear policies
    Policy.objects.all().delete()

    # Reset is_admin to False
    Role.objects.update(is_admin=False)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0006_policy_role_is_admin_alter_role_permissions_and_more"),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
