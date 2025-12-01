from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.utils.models import BaseModel


class Invoice(BaseModel):
    """Model representing an invoice for a consultation."""

    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("pending", _("Pending")),
        ("paid", _("Paid")),
        ("cancelled", _("Cancelled")),
    ]

    DISCOUNT_TYPE_CHOICES = [
        ("none", _("None")),
        ("amount", _("Fixed Amount")),
        ("percent", _("Percentage")),
    ]

    # Relationships
    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    consultation = models.OneToOneField(
        "consultations.Consultation",
        on_delete=models.CASCADE,
        related_name="invoice",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    created_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        related_name="invoices",
        null=True,
        blank=True,
    )

    # Invoice Information
    invoice_id = models.CharField(
        max_length=20,
        help_text=_("Unique invoice ID (e.g., INV-2025-0001)"),
    )
    invoice_date = models.DateField()

    # Totals
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Sum of all line items"),
    )
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default="none",
    )
    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Discount amount or percentage"),
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Calculated discount amount"),
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Final amount after discount"),
    )

    # Payment (single payment - no partial payments)
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Date and time of payment"),
    )
    payment_method = models.CharField(
        max_length=20,
        default="cash",
        help_text=_("Payment method (cash only for now)"),
    )
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text=_("Receipt number or reference"),
    )

    # Status and notes
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text=_("Additional notes"),
    )

    class Meta:
        ordering = ["-invoice_date", "-created_at"]
        unique_together = ["clinic", "invoice_id"]
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")

    def __str__(self):
        return f"{self.invoice_id} - {self.patient}"

    @property
    def patient_name(self):
        return self.patient.full_name if self.patient else ""

    @property
    def created_by_name(self):
        if self.created_by:
            return self.created_by.get_full_name() or self.created_by.email
        return ""

    @property
    def item_count(self):
        return self.items.count()

    @property
    def balance(self):
        return self.total - self.amount_paid

    def calculate_totals(self):
        """Calculate subtotal, discount_amount, and total from items."""
        self.subtotal = sum(item.amount for item in self.items.all())

        if self.discount_type == "percent" and self.discount_value > 0:
            self.discount_amount = (self.subtotal * self.discount_value) / Decimal("100")
        elif self.discount_type == "amount" and self.discount_value > 0:
            self.discount_amount = self.discount_value
        else:
            self.discount_amount = Decimal("0.00")

        self.total = self.subtotal - self.discount_amount


class InvoiceItem(BaseModel):
    """Model representing a single line item in an invoice."""

    # Relationships
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )
    service = models.ForeignKey(
        "clinic.Service",
        on_delete=models.SET_NULL,
        related_name="invoice_items",
        null=True,
        blank=True,
        help_text=_("Reference to service (optional)"),
    )

    # Item Information (stored for historical preservation)
    description = models.CharField(
        max_length=255,
        help_text=_("Item description"),
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text=_("Quantity"),
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=_("Price per unit"),
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=_("Total amount (quantity × unit_price)"),
    )

    class Meta:
        ordering = ["id"]
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")

    def __str__(self):
        return f"{self.description} - {self.amount}"

    def save(self, *args, **kwargs):
        # Auto-calculate amount
        self.amount = Decimal(str(self.quantity)) * self.unit_price
        super().save(*args, **kwargs)
