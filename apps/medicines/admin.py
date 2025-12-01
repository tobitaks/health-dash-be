from django.contrib import admin

from apps.medicines.models import Medicine


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = [
        "generic_name",
        "brand_name",
        "strength",
        "form",
        "category",
        "clinic",
        "is_active",
    ]
    list_filter = ["form", "category", "is_active", "clinic"]
    search_fields = ["generic_name", "brand_name"]
    ordering = ["generic_name", "strength"]
