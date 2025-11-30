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

    BLOOD_TYPE_CHOICES = [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
        ("Unknown", "Unknown"),
    ]

    RELATIONSHIP_CHOICES = [
        ("Spouse", "Spouse"),
        ("Parent", "Parent"),
        ("Sibling", "Sibling"),
        ("Child", "Child"),
        ("Friend", "Friend"),
        ("Other", "Other"),
    ]

    CIVIL_STATUS_CHOICES = [
        ("Single", "Single"),
        ("Married", "Married"),
        ("Widowed", "Widowed"),
        ("Separated", "Separated"),
        ("Divorced", "Divorced"),
    ]

    # Basic Info (required)
    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.CASCADE,
        related_name="patients",
    )
    patient_id = models.CharField(max_length=20)  # PT-YYYY-####
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, default="")  # Optional
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS_CHOICES, blank=True, default="")  # Optional
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Contact Information (optional)
    email = models.EmailField(blank=True, default="")
    address_street = models.CharField(max_length=255, blank=True, default="")
    address_city = models.CharField(max_length=100, blank=True, default="")
    address_province = models.CharField(max_length=100, blank=True, default="")
    address_zip = models.CharField(max_length=20, blank=True, default="")

    # Emergency Contact (optional)
    emergency_contact_name = models.CharField(max_length=200, blank=True, default="")
    emergency_contact_phone = models.CharField(max_length=20, blank=True, default="")
    emergency_contact_relationship = models.CharField(
        max_length=20, choices=RELATIONSHIP_CHOICES, blank=True, default=""
    )

    # Medical Information (optional)
    blood_type = models.CharField(max_length=10, choices=BLOOD_TYPE_CHOICES, blank=True, default="")
    allergies = models.JSONField(default=list, blank=True)  # List of allergy strings
    medical_conditions = models.JSONField(default=list, blank=True)  # List of condition strings
    current_medications = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ["clinic", "patient_id"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.patient_id} - {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
