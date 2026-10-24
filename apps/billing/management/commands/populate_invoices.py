"""
Management command to populate invoices for demo.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.billing.models import Invoice, InvoiceItem
from apps.clinic.models import Service
from apps.consultations.models import Consultation
from apps.users.models import CustomUser


class Command(BaseCommand):
    help = "Populate invoices for consultations"

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
            help="Clear existing invoices before populating",
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

        self.stdout.write(f"Populating invoices for clinic: {clinic.name}")

        # Get consultations without invoices
        consultations = list(
            Consultation.objects.filter(clinic=clinic)
            .exclude(invoice__isnull=False)
            .select_related("patient")
        )

        if not consultations:
            self.stdout.write(self.style.WARNING("No consultations without invoices found."))
            return

        services = list(Service.objects.filter(clinic=clinic, is_active=True))
        if not services:
            raise CommandError("No services found. Run populate_services first.") from None

        # Clear existing invoices if requested
        if clear:
            deleted_count = Invoice.objects.filter(clinic=clinic).delete()[0]
            self.stdout.write(self.style.WARNING(f"Cleared {deleted_count} existing invoices"))
            # Re-fetch consultations after clearing
            consultations = list(
                Consultation.objects.filter(clinic=clinic)
                .select_related("patient")
            )

        # Get next invoice number
        existing_count = Invoice.objects.filter(clinic=clinic).count()
        current_year = date.today().year

        created_count = 0

        for consultation in consultations:
            invoice_number = existing_count + created_count + 1
            invoice_id = f"INV-{current_year}-{invoice_number:04d}"

            # Check if already exists
            if Invoice.objects.filter(clinic=clinic, invoice_id=invoice_id).exists():
                continue

            # Determine status based on consultation date
            days_old = (date.today() - consultation.consultation_date).days

            if days_old > 30:
                # Old consultations: mostly paid
                status = random.choices(
                    ["paid", "cancelled"],
                    weights=[90, 10],
                    k=1
                )[0]
            elif days_old > 7:
                # Week-old: mix of paid and pending
                status = random.choices(
                    ["paid", "pending", "draft"],
                    weights=[60, 30, 10],
                    k=1
                )[0]
            else:
                # Recent: more drafts and pending
                status = random.choices(
                    ["draft", "pending", "paid"],
                    weights=[40, 40, 20],
                    k=1
                )[0]

            # Create invoice
            invoice = Invoice.objects.create(
                clinic=clinic,
                consultation=consultation,
                patient=consultation.patient,
                created_by=user,
                invoice_id=invoice_id,
                invoice_date=consultation.consultation_date,
                status=status,
            )

            # Add invoice items (1-3 services per invoice)
            num_items = random.randint(1, 3)
            selected_services = random.sample(services, min(num_items, len(services)))

            for service in selected_services:
                quantity = 1
                InvoiceItem.objects.create(
                    invoice=invoice,
                    service=service,
                    description=service.name,
                    quantity=quantity,
                    unit_price=service.price,
                    amount=service.price * quantity,
                )

            # Calculate totals
            invoice.calculate_totals()

            # Add discount occasionally (20% chance)
            if random.random() < 0.2:
                if random.random() < 0.5:
                    # Percentage discount
                    invoice.discount_type = "percent"
                    invoice.discount_value = Decimal(random.choice(["5", "10", "15", "20"]))
                else:
                    # Fixed amount discount
                    invoice.discount_type = "amount"
                    invoice.discount_value = Decimal(random.choice(["50", "100", "150"]))
                invoice.calculate_totals()

            # Set payment info for paid invoices
            if status == "paid":
                invoice.amount_paid = invoice.total
                invoice.payment_date = timezone.now() - timedelta(days=random.randint(0, days_old))
                invoice.payment_method = "cash"
                invoice.payment_reference = f"REC-{random.randint(1000, 9999)}"

            invoice.save()
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_count} invoices for {clinic.name}")
        )
