"""
Management command to populate clinic services.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from apps.clinic.models import Service
from apps.users.models import CustomUser

# Common clinic services
CLINIC_SERVICES = [
    {
        "name": "General Consultation",
        "code": "CONS-GEN",
        "price": Decimal("500.00"),
        "duration_minutes": 30,
    },
    {
        "name": "Follow-up Consultation",
        "code": "CONS-FU",
        "price": Decimal("350.00"),
        "duration_minutes": 20,
    },
    {
        "name": "Pediatric Consultation",
        "code": "CONS-PED",
        "price": Decimal("600.00"),
        "duration_minutes": 30,
    },
    {
        "name": "Senior Citizen Consultation",
        "code": "CONS-SC",
        "price": Decimal("400.00"),
        "duration_minutes": 30,
    },
    {
        "name": "Blood Pressure Monitoring",
        "code": "PROC-BP",
        "price": Decimal("100.00"),
        "duration_minutes": 10,
    },
    {
        "name": "Blood Glucose Test",
        "code": "LAB-GLU",
        "price": Decimal("150.00"),
        "duration_minutes": 15,
    },
    {
        "name": "Complete Blood Count (CBC)",
        "code": "LAB-CBC",
        "price": Decimal("350.00"),
        "duration_minutes": 15,
    },
    {
        "name": "Urinalysis",
        "code": "LAB-UA",
        "price": Decimal("200.00"),
        "duration_minutes": 10,
    },
    {
        "name": "Wound Dressing",
        "code": "PROC-WD",
        "price": Decimal("250.00"),
        "duration_minutes": 20,
    },
    {
        "name": "Medical Certificate",
        "code": "DOC-MC",
        "price": Decimal("200.00"),
        "duration_minutes": 15,
    },
    {
        "name": "ECG / Electrocardiogram",
        "code": "PROC-ECG",
        "price": Decimal("500.00"),
        "duration_minutes": 20,
    },
    {
        "name": "Nebulization",
        "code": "PROC-NEB",
        "price": Decimal("300.00"),
        "duration_minutes": 20,
    },
]


class Command(BaseCommand):
    help = "Populate clinic services"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Email of the clinic owner",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing services before populating",
        )

    def handle(self, *args, **options):
        email = options["email"]
        clear = options["clear"]

        # Get the user and their clinic
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise CommandError(f"User with email '{email}' not found") from None

        clinic = user.clinic
        if not clinic:
            raise CommandError(f"User '{email}' has no associated clinic") from None

        self.stdout.write(f"Populating services for clinic: {clinic.name}")

        # Clear existing services if requested
        if clear:
            deleted_count = Service.objects.filter(clinic=clinic).delete()[0]
            self.stdout.write(self.style.WARNING(f"Cleared {deleted_count} existing services"))

        # Create services
        created_count = 0
        skipped_count = 0

        for service_data in CLINIC_SERVICES:
            # Check if service already exists
            exists = Service.objects.filter(
                clinic=clinic,
                code=service_data["code"],
            ).exists()

            if exists:
                skipped_count += 1
                continue

            Service.objects.create(
                clinic=clinic,
                **service_data,
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_count} services, skipped {skipped_count} (already exist)")
        )
