from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.utils.models import BaseModel


class LabOrder(BaseModel):
    """Model representing a lab order for a consultation."""

    STATUS_CHOICES = [
        ("ordered", _("Ordered")),
        ("collected", _("Sample Collected")),
        ("processing", _("Processing")),
        ("results_available", _("Results Available")),
        ("reviewed", _("Reviewed")),
        ("cancelled", _("Cancelled")),
    ]

    PRIORITY_CHOICES = [
        ("routine", _("Routine")),
        ("urgent", _("Urgent")),
        ("stat", _("STAT")),
    ]

    # Relationships
    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.CASCADE,
        related_name="lab_orders",
    )
    consultation = models.ForeignKey(
        "consultations.Consultation",
        on_delete=models.CASCADE,
        related_name="lab_orders",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="lab_orders",
    )
    ordered_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        related_name="lab_orders_created",
    )

    # Order Information
    order_id = models.CharField(
        max_length=20,
        help_text=_("Unique order ID (e.g., LAB-2025-0001)"),
    )
    order_date = models.DateField(
        help_text=_("Date the order was created"),
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="routine",
        help_text=_("Order priority"),
    )
    clinical_indication = models.TextField(
        blank=True,
        default="",
        help_text=_("Clinical reason for ordering the tests"),
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text=_("Additional notes"),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ordered",
        help_text=_("Current status of the order"),
    )

    class Meta:
        ordering = ["-order_date", "-created_at"]
        unique_together = ["clinic", "order_id"]
        verbose_name = _("Lab Order")
        verbose_name_plural = _("Lab Orders")

    def __str__(self):
        return f"{self.order_id} - {self.patient}"

    @property
    def test_count(self):
        """Returns the number of tests in this order."""
        return self.items.count()

    @property
    def patient_name(self):
        """Returns the patient's full name."""
        return self.patient.full_name if self.patient else None

    @property
    def doctor_name(self):
        """Returns the ordering doctor's name."""
        if self.ordered_by:
            name = f"{self.ordered_by.first_name} {self.ordered_by.last_name}".strip()
            return name or self.ordered_by.email
        return None


class LabOrderItem(BaseModel):
    """Model representing an individual test in a lab order."""

    # Relationships
    lab_order = models.ForeignKey(
        LabOrder,
        on_delete=models.CASCADE,
        related_name="items",
    )
    lab_test = models.ForeignKey(
        "lab_orders.LabTest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        help_text=_("Reference to test catalog (optional for historical preservation)"),
    )

    # Test Information (stored for historical data)
    test_name = models.CharField(
        max_length=200,
        help_text=_("Name of the test"),
    )
    test_code = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text=_("Test code"),
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text=_("Test category"),
    )
    sample_type = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text=_("Sample type required"),
    )

    # Item-specific Information
    special_instructions = models.TextField(
        blank=True,
        default="",
        help_text=_("Special instructions for this test"),
    )

    # Results (to be filled when results are available)
    result = models.TextField(
        blank=True,
        default="",
        help_text=_("Test result"),
    )
    result_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Date/time when result was recorded"),
    )
    is_abnormal = models.BooleanField(
        default=False,
        help_text=_("Whether the result is abnormal"),
    )
    result_notes = models.TextField(
        blank=True,
        default="",
        help_text=_("Notes about the result"),
    )

    class Meta:
        ordering = ["id"]
        verbose_name = _("Lab Order Item")
        verbose_name_plural = _("Lab Order Items")

    def __str__(self):
        return f"{self.test_name} - {self.lab_order.order_id}"

    @property
    def display_name(self):
        """Returns a formatted display name."""
        if self.test_code:
            return f"{self.test_name} ({self.test_code})"
        return self.test_name
