from django.db import models

from apps.utils.models import BaseModel


class Appointment(BaseModel):
    """
    Appointment model - represents a scheduled appointment at a clinic.
    Links patients to services with a specific date/time.
    """

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("confirmed", "Confirmed"),
        ("in-progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("no-show", "No Show"),
    ]

    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    appointment_id = models.CharField(max_length=20)  # APT-YYYY-####
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    service = models.ForeignKey(
        "clinic.Service",
        on_delete=models.SET_NULL,
        null=True,
        related_name="appointments",
    )
    assigned_to = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_appointments",
        help_text="Staff member assigned to this appointment",
    )
    date = models.DateField()
    time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ["clinic", "appointment_id"]
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.appointment_id} - {self.patient.full_name} ({self.date})"
