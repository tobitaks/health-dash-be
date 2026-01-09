from django.contrib import admin

from apps.consultations.models import Consultation


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = (
        "consultation_id",
        "patient",
        "consultation_date",
        "consultation_time",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "consultation_date", "clinic")
    search_fields = (
        "consultation_id",
        "patient__first_name",
        "patient__last_name",
        "patient__patient_id",
        "chief_complaint",
        "primary_diagnosis",
    )
    readonly_fields = ("consultation_id", "created_at", "updated_at")
    ordering = ("-consultation_date", "-consultation_time")
