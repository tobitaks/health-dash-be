from django.db import models

from apps.utils.models import BaseModel


class Service(BaseModel):
    """
    Service model - represents a service offering by a clinic.
    Each clinic has its own set of services.
    """

    clinic = models.ForeignKey(
        "clinic.Clinic",
        on_delete=models.CASCADE,
        related_name="services",
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.PositiveIntegerField(default=30, help_text="Default duration in minutes")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["clinic", "code"]
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"
