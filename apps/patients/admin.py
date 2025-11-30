from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_id", "first_name", "last_name", "gender", "phone", "status", "clinic")
    list_filter = ("status", "gender", "clinic")
    search_fields = ("patient_id", "first_name", "last_name", "phone")
    ordering = ("-created_at",)
