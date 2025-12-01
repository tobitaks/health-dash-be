from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.utils.models import BaseModel


class Medicine(BaseModel):
    """Model representing a medicine in the clinic's formulary."""

    FORM_CHOICES = [
        ("tablet", _("Tablet")),
        ("capsule", _("Capsule")),
        ("syrup", _("Syrup")),
        ("suspension", _("Suspension")),
        ("injection", _("Injection")),
        ("cream", _("Cream")),
        ("ointment", _("Ointment")),
        ("gel", _("Gel")),
        ("drops", _("Drops")),
        ("inhaler", _("Inhaler")),
        ("nasal_spray", _("Nasal Spray")),
        ("powder", _("Powder")),
        ("softgel", _("Softgel")),
        ("suppository", _("Suppository")),
        ("patch", _("Patch")),
        ("solution", _("Solution")),
        ("lotion", _("Lotion")),
        ("nebule", _("Nebule")),
    ]

    CATEGORY_CHOICES = [
        ("antibiotic", _("Antibiotic")),
        ("analgesic", _("Analgesic/Pain Reliever")),
        ("antipyretic", _("Antipyretic/Fever Reducer")),
        ("antihistamine", _("Antihistamine")),
        ("antihypertensive", _("Antihypertensive")),
        ("antidiabetic", _("Antidiabetic")),
        ("antacid", _("Antacid/GI")),
        ("bronchodilator", _("Bronchodilator")),
        ("corticosteroid", _("Corticosteroid")),
        ("vitamin", _("Vitamin/Supplement")),
        ("nsaid", _("NSAID")),
        ("antiemetic", _("Antiemetic")),
        ("antidiarrheal", _("Antidiarrheal")),
        ("laxative", _("Laxative")),
        ("antifungal", _("Antifungal")),
        ("antiviral", _("Antiviral")),
        ("cardiovascular", _("Cardiovascular")),
        ("cns", _("CNS/Neurological")),
        ("dermatological", _("Dermatological")),
        ("ophthalmic", _("Ophthalmic")),
        ("otic", _("Otic/Ear")),
        ("other", _("Other")),
    ]

    # Relationships
    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.CASCADE,
        related_name="medicines",
    )

    # Medicine Information
    generic_name = models.CharField(
        max_length=200,
        help_text=_("Generic/scientific name of the medicine"),
    )
    brand_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text=_("Brand/trade name of the medicine"),
    )
    strength = models.CharField(
        max_length=50,
        help_text=_("Strength/dosage (e.g., 500mg, 125mg/5ml)"),
    )
    form = models.CharField(
        max_length=20,
        choices=FORM_CHOICES,
        help_text=_("Pharmaceutical form"),
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="other",
        help_text=_("Medicine category"),
    )

    # Default Prescription Values
    default_sig = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text=_("Default prescription instructions (Signa)"),
    )
    default_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Default quantity to prescribe"),
    )

    # Additional Information
    notes = models.TextField(
        blank=True,
        default="",
        help_text=_("Additional notes or instructions"),
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this medicine is currently available"),
    )

    class Meta:
        ordering = ["generic_name", "strength"]
        unique_together = ["clinic", "generic_name", "strength", "form"]
        verbose_name = _("Medicine")
        verbose_name_plural = _("Medicines")

    def __str__(self):
        name = self.generic_name
        if self.brand_name:
            name = f"{name} ({self.brand_name})"
        return f"{name} {self.strength} {self.get_form_display()}"

    @property
    def display_name(self):
        """Returns a formatted display name for the medicine."""
        return f"{self.generic_name} {self.strength} {self.get_form_display()}"

    @property
    def full_name(self):
        """Returns full name including brand if available."""
        if self.brand_name:
            return f"{self.generic_name} ({self.brand_name}) {self.strength} {self.get_form_display()}"
        return self.display_name
