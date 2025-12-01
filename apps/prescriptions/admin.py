from django.contrib import admin

from apps.prescriptions.models import Prescription, PrescriptionItem


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1
    fields = ["medicine_name", "strength", "form", "sig", "quantity", "notes"]


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = [
        "prescription_id",
        "patient",
        "prescription_date",
        "status",
        "medicine_count",
        "prescribed_by",
    ]
    list_filter = ["status", "prescription_date", "clinic"]
    search_fields = ["prescription_id", "patient__first_name", "patient__last_name"]
    ordering = ["-prescription_date", "-created_at"]
    inlines = [PrescriptionItemInline]


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ["prescription", "medicine_name", "strength", "form", "quantity"]
    list_filter = ["prescription__clinic"]
    search_fields = ["medicine_name", "prescription__prescription_id"]
