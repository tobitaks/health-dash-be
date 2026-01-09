from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "clinic",
        "role",
        "is_owner",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "role", "is_owner", "clinic", "groups", "date_joined")
    ordering = ("-date_joined",)

    fieldsets = UserAdmin.fieldsets + (
        ("Clinic", {"fields": ("clinic", "role", "is_owner")}),
        ("Custom Fields", {"fields": ("avatar", "subscription", "customer", "language", "timezone")}),
    )  # type: ignore
