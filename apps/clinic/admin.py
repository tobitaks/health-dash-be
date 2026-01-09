from django.contrib import admin

from .models import Clinic


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "address_city", "is_active", "created_at"]
    list_filter = ["is_active", "address_city", "created_at"]
    search_fields = ["name", "email", "phone", "address_city"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("name", "is_active")}),
        ("Contact Information", {"fields": ("email", "phone", "mobile", "website")}),
        (
            "Address",
            {
                "fields": (
                    "address_street",
                    "address_city",
                    "address_state",
                    "address_postal_code",
                    "address_country",
                )
            },
        ),
        ("Settings", {"fields": ("timezone", "currency", "logo", "business_hours")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
