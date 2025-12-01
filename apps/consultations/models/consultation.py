from django.db import models

from apps.utils.models import BaseModel


class Consultation(BaseModel):
    """Model representing a patient consultation/visit."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("completed", "Completed"),
    ]

    TEMPERATURE_UNIT_CHOICES = [
        ("C", "Celsius"),
        ("F", "Fahrenheit"),
    ]

    WEIGHT_UNIT_CHOICES = [
        ("kg", "Kilograms"),
        ("lbs", "Pounds"),
    ]

    HEIGHT_UNIT_CHOICES = [
        ("cm", "Centimeters"),
        ("in", "Inches"),
    ]

    # Relationships
    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.CASCADE,
        related_name="consultations",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="consultations",
    )
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.SET_NULL,
        related_name="consultations",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        related_name="consultations",
        null=True,
        blank=True,
    )

    # Basic Information
    consultation_id = models.CharField(max_length=20)  # CONS-YYYY-####
    consultation_date = models.DateField()
    consultation_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )
    chief_complaint = models.TextField()

    # Vital Signs
    bp_systolic = models.PositiveIntegerField(null=True, blank=True)
    bp_diastolic = models.PositiveIntegerField(null=True, blank=True)
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )
    temperature_unit = models.CharField(
        max_length=1,
        choices=TEMPERATURE_UNIT_CHOICES,
        default="C",
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
    )
    weight_unit = models.CharField(
        max_length=3,
        choices=WEIGHT_UNIT_CHOICES,
        default="kg",
    )
    height = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
    )
    height_unit = models.CharField(
        max_length=2,
        choices=HEIGHT_UNIT_CHOICES,
        default="cm",
    )
    heart_rate = models.PositiveIntegerField(null=True, blank=True)
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    oxygen_saturation = models.PositiveIntegerField(null=True, blank=True)

    # SOAP Notes
    soap_subjective = models.TextField(blank=True, default="")
    soap_objective = models.TextField(blank=True, default="")
    soap_assessment = models.TextField(blank=True, default="")
    soap_plan = models.TextField(blank=True, default="")

    # Structured Diagnosis (part of Assessment)
    primary_diagnosis = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Primary/working diagnosis",
    )
    secondary_diagnoses = models.JSONField(
        default=list,
        blank=True,
        help_text="List of secondary diagnoses",
    )
    differential_diagnoses = models.JSONField(
        default=list,
        blank=True,
        help_text="List of differential diagnoses to consider",
    )

    # Physical Examination (structured by body system)
    physical_exam = models.JSONField(
        default=dict,
        blank=True,
        help_text="Physical exam findings by system: general, heent, neck, chest, cvs, abdomen, extremities, neuro",
    )

    # Additional Information
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ["clinic", "consultation_id"]
        ordering = ["-consultation_date", "-consultation_time"]

    def __str__(self):
        return f"{self.consultation_id} - {self.patient}"

    @property
    def patient_name(self):
        return self.patient.full_name if self.patient else ""

    @property
    def blood_pressure(self):
        if self.bp_systolic and self.bp_diastolic:
            return f"{self.bp_systolic}/{self.bp_diastolic}"
        return None
