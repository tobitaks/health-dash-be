"""
Master command to populate all demo data for a clinic.
Runs all populate commands in the correct order.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.users.models import CustomUser


class Command(BaseCommand):
    help = "Populate all demo data for a clinic (services, patients, medicines, appointments, consultations, invoices)"

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
            help="Clear existing data before populating",
        )
        parser.add_argument(
            "--patients",
            type=int,
            default=25,
            help="Number of patients to create (default: 25)",
        )
        parser.add_argument(
            "--appointments",
            type=int,
            default=35,
            help="Number of appointments to create (default: 35)",
        )
        parser.add_argument(
            "--consultations",
            type=int,
            default=25,
            help="Number of consultations to create (default: 25)",
        )

    def handle(self, *args, **options):
        email = options["email"]
        clear = options["clear"]
        patient_count = options["patients"]
        appointment_count = options["appointments"]
        consultation_count = options["consultations"]

        # Validate user exists
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise CommandError(f"User with email '{email}' not found") from None

        if not user.clinic:
            raise CommandError(f"User '{email}' has no associated clinic") from None

        self.stdout.write(self.style.HTTP_INFO(f"\n{'='*50}"))
        self.stdout.write(self.style.HTTP_INFO(f"Populating demo data for: {user.clinic.name}"))
        self.stdout.write(self.style.HTTP_INFO(f"{'='*50}\n"))

        # 1. Services (needed for appointments and invoices)
        self.stdout.write(self.style.MIGRATE_HEADING("\n[1/6] Populating services..."))
        call_command("populate_services", email=email, clear=clear)

        # 2. Patients
        self.stdout.write(self.style.MIGRATE_HEADING("\n[2/6] Populating patients..."))
        call_command("populate_patients", email=email, count=patient_count, clear=clear)

        # 3. Medicines
        self.stdout.write(self.style.MIGRATE_HEADING("\n[3/6] Populating medicines..."))
        call_command("populate_medicines", email=email, clear=clear)

        # 4. Appointments (needs patients and services)
        self.stdout.write(self.style.MIGRATE_HEADING("\n[4/6] Populating appointments..."))
        call_command("populate_appointments", email=email, count=appointment_count, clear=clear)

        # 5. Consultations (needs patients)
        self.stdout.write(self.style.MIGRATE_HEADING("\n[5/6] Populating consultations..."))
        call_command("populate_consultations", email=email, count=consultation_count, clear=clear)

        # 6. Invoices (needs consultations and services)
        self.stdout.write(self.style.MIGRATE_HEADING("\n[6/6] Populating invoices..."))
        call_command("populate_invoices", email=email, clear=clear)

        self.stdout.write(self.style.SUCCESS(f"\n{'='*50}"))
        self.stdout.write(self.style.SUCCESS("Demo data population complete!"))
        self.stdout.write(self.style.SUCCESS(f"{'='*50}\n"))
