"""
Management command to populate appointments for demo.
"""

import random
from datetime import date, time, timedelta

from django.core.management.base import BaseCommand, CommandError

from apps.appointments.models import Appointment
from apps.clinic.models import Service
from apps.patients.models import Patient
from apps.users.models import CustomUser


class Command(BaseCommand):
    help = "Populate appointments for a clinic (last 2 months + upcoming)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Email of the clinic owner",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=35,
            help="Number of appointments to create (default: 35)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing appointments before populating",
        )

    def handle(self, *args, **options):
        email = options["email"]
        count = options["count"]
        clear = options["clear"]

        # Get the user and their clinic
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise CommandError(f"User with email '{email}' not found") from None

        clinic = user.clinic
        if not clinic:
            raise CommandError(f"User '{email}' has no associated clinic") from None

        self.stdout.write(f"Populating appointments for clinic: {clinic.name}")

        # Get patients and services
        patients = list(Patient.objects.filter(clinic=clinic, status="active"))
        services = list(Service.objects.filter(clinic=clinic, is_active=True))

        if not patients:
            raise CommandError("No active patients found. Run populate_patients first.") from None

        if not services:
            raise CommandError("No services found. Run populate_services first.") from None

        # Clear existing appointments if requested
        if clear:
            deleted_count = Appointment.objects.filter(clinic=clinic).delete()[0]
            self.stdout.write(self.style.WARNING(f"Cleared {deleted_count} existing appointments"))

        # Get next appointment number
        existing_count = Appointment.objects.filter(clinic=clinic).count()
        current_year = date.today().year

        # Time slots (8 AM to 5 PM)
        time_slots = [
            time(8, 0), time(8, 30), time(9, 0), time(9, 30),
            time(10, 0), time(10, 30), time(11, 0), time(11, 30),
            time(13, 0), time(13, 30), time(14, 0), time(14, 30),
            time(15, 0), time(15, 30), time(16, 0), time(16, 30),
        ]

        created_count = 0
        today = date.today()

        for i in range(count):
            appointment_number = existing_count + i + 1
            appointment_id = f"APT-{current_year}-{appointment_number:04d}"

            # Check if already exists
            if Appointment.objects.filter(clinic=clinic, appointment_id=appointment_id).exists():
                self.stdout.write(self.style.WARNING(f"Appointment {appointment_id} exists, skipping."))
                continue

            # Generate date: 70% past (last 2 months), 30% future (next 2 weeks)
            if random.random() < 0.7:
                # Past appointments (last 60 days)
                days_ago = random.randint(1, 60)
                appt_date = today - timedelta(days=days_ago)
                # Past appointments have completed/cancelled/no-show status
                status = random.choices(
                    ["completed", "cancelled", "no-show"],
                    weights=[80, 15, 5],
                    k=1
                )[0]
            else:
                # Future appointments (next 14 days)
                days_ahead = random.randint(1, 14)
                appt_date = today + timedelta(days=days_ahead)
                # Future appointments are scheduled/confirmed
                status = random.choices(
                    ["scheduled", "confirmed"],
                    weights=[60, 40],
                    k=1
                )[0]

            appt_time = random.choice(time_slots)
            patient = random.choice(patients)
            service = random.choice(services)

            Appointment.objects.create(
                clinic=clinic,
                appointment_id=appointment_id,
                patient=patient,
                service=service,
                assigned_to=user,
                date=appt_date,
                time=appt_time,
                duration_minutes=service.duration_minutes,
                status=status,
                notes="" if random.random() > 0.3 else random.choice([
                    "First visit",
                    "Follow-up required",
                    "Patient requested morning slot",
                    "Referred by Dr. Santos",
                    "Insurance claim pending",
                ]),
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_count} appointments for {clinic.name}")
        )
