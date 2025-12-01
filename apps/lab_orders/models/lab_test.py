from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.utils.models import BaseModel


class LabTest(BaseModel):
    """Model representing a lab test in the clinic's catalog."""

    CATEGORY_CHOICES = [
        ("hematology", _("Hematology")),
        ("chemistry", _("Chemistry")),
        ("urinalysis", _("Urinalysis")),
        ("microbiology", _("Microbiology")),
        ("imaging", _("Imaging")),
        ("cardiology", _("Cardiology")),
        ("other", _("Other")),
    ]

    SAMPLE_TYPE_CHOICES = [
        ("blood", _("Blood")),
        ("urine", _("Urine")),
        ("stool", _("Stool")),
        ("swab", _("Swab")),
        ("tissue", _("Tissue")),
        ("sputum", _("Sputum")),
        ("csf", _("CSF")),
        ("none", _("None (Imaging)")),
        ("other", _("Other")),
    ]

    # Relationships
    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.CASCADE,
        related_name="lab_tests",
    )

    # Test Information
    name = models.CharField(
        max_length=200,
        help_text=_("Name of the lab test"),
    )
    code = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text=_("Test code (e.g., CBC, CMP)"),
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="other",
        help_text=_("Test category"),
    )
    sample_type = models.CharField(
        max_length=20,
        choices=SAMPLE_TYPE_CHOICES,
        default="blood",
        help_text=_("Type of sample required"),
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text=_("Description of the test"),
    )
    turnaround_time = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text=_("Expected turnaround time (e.g., 24-48 hours)"),
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Price of the test"),
    )
    special_instructions = models.TextField(
        blank=True,
        default="",
        help_text=_("Default special instructions (e.g., fasting required)"),
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this test is currently available"),
    )

    class Meta:
        ordering = ["category", "name"]
        unique_together = ["clinic", "name"]
        verbose_name = _("Lab Test")
        verbose_name_plural = _("Lab Tests")

    def __str__(self):
        if self.code:
            return f"{self.name} ({self.code})"
        return self.name

    @property
    def display_name(self):
        """Returns a formatted display name for the test."""
        if self.code:
            return f"{self.name} ({self.code})"
        return self.name
