from django.db import models

from apps.utils.models import BaseModel


class Patient(BaseModel):
    """
    Patient model - represents a patient of a clinic.
    Each clinic has its own set of patients (multi-tenant).
    """

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("archived", "Archived"),
    ]

    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.CASCADE,
        related_name="patients",
    )
    patient_id = models.CharField(max_length=20)  # PT-YYYY-####
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        unique_together = ["clinic", "patient_id"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.patient_id} - {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
