from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.utils.models import BaseModel


class Prescription(BaseModel):
    """Model representing a prescription issued during a consultation."""

    STATUS_CHOICES = [
        ("active", _("Active")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    ]

    # Relationships
    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.CASCADE,
        related_name="prescriptions",
    )
    consultation = models.OneToOneField(
        "consultations.Consultation",
        on_delete=models.CASCADE,
        related_name="prescription",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="prescriptions",
    )
    prescribed_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        related_name="prescriptions",
        null=True,
        blank=True,
    )

    # Prescription Information
    prescription_id = models.CharField(
        max_length=20,
        help_text=_("Unique prescription ID (e.g., RX-2025-0001)"),
    )
    prescription_date = models.DateField()
    # Diagnosis removed - now lives in Consultation.diagnoses (primary, secondary, differential)
    notes = models.TextField(
        blank=True,
        default="",
        help_text=_("Additional notes or instructions"),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    class Meta:
        ordering = ["-prescription_date", "-created_at"]
        unique_together = ["clinic", "prescription_id"]
        verbose_name = _("Prescription")
        verbose_name_plural = _("Prescriptions")

    def __str__(self):
        return f"{self.prescription_id} - {self.patient}"

    @property
    def patient_name(self):
        return self.patient.full_name if self.patient else ""

    @property
    def doctor_name(self):
        if self.prescribed_by:
            return self.prescribed_by.get_full_name() or self.prescribed_by.email
        return ""

    @property
    def medicine_count(self):
        return self.items.count()


class PrescriptionItem(BaseModel):
    """Model representing a single medicine item in a prescription."""

    # Relationships
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="items",
    )
    medicine = models.ForeignKey(
        "medicines.Medicine",
        on_delete=models.SET_NULL,
        related_name="prescription_items",
        null=True,
        blank=True,
        help_text=_("Reference to medicine in formulary (optional)"),
    )

    # Medicine Information (stored to preserve historical data)
    medicine_name = models.CharField(
        max_length=300,
        help_text=_("Medicine name (generic + brand if applicable)"),
    )
    strength = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text=_("Strength/dosage (e.g., 500mg)"),
    )
    form = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text=_("Pharmaceutical form (e.g., Tablet, Capsule)"),
    )

    # Prescription Details
    sig = models.CharField(
        max_length=500,
        help_text=_("Prescription instructions (Signa)"),
    )
    quantity = models.PositiveIntegerField(
        help_text=_("Quantity to dispense"),
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text=_("Additional notes for this medicine"),
    )

    class Meta:
        ordering = ["id"]
        verbose_name = _("Prescription Item")
        verbose_name_plural = _("Prescription Items")

    def __str__(self):
        return f"{self.medicine_name} - {self.sig}"

    @property
    def display_name(self):
        """Returns formatted medicine name with strength and form."""
        parts = [self.medicine_name]
        if self.strength:
            parts.append(self.strength)
        if self.form:
            parts.append(self.form)
        return " ".join(parts)
