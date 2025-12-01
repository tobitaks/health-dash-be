from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.lab_orders.models import LabTest, LabOrder, LabOrderItem


class LabOrderItemInline(admin.TabularInline):
    """Inline admin for LabOrderItem."""

    model = LabOrderItem
    extra = 1
    fields = [
        "lab_test",
        "test_name",
        "test_code",
        "category",
        "sample_type",
        "result",
        "is_abnormal",
    ]
    readonly_fields = []
    autocomplete_fields = ["lab_test"]


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    """Admin configuration for LabTest model."""

    list_display = [
        "name",
        "code",
        "category",
        "sample_type",
        "clinic",
        "is_active",
    ]
    list_filter = [
        "category",
        "sample_type",
        "is_active",
        "clinic",
    ]
    search_fields = [
        "name",
        "code",
        "description",
    ]
    ordering = ["category", "name"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "clinic",
                    "name",
                    "code",
                    "category",
                    "sample_type",
                ]
            },
        ),
        (
            _("Details"),
            {
                "fields": [
                    "description",
                    "turnaround_time",
                    "price",
                    "special_instructions",
                    "is_active",
                ]
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]


@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    """Admin configuration for LabOrder model."""

    list_display = [
        "order_id",
        "patient",
        "consultation",
        "status",
        "priority",
        "order_date",
        "clinic",
    ]
    list_filter = [
        "status",
        "priority",
        "order_date",
        "clinic",
    ]
    search_fields = [
        "order_id",
        "patient__first_name",
        "patient__last_name",
        "clinical_indication",
    ]
    ordering = ["-order_date", "-created_at"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [LabOrderItemInline]
    autocomplete_fields = ["patient", "consultation", "ordered_by"]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "clinic",
                    "order_id",
                    "consultation",
                    "patient",
                    "ordered_by",
                ]
            },
        ),
        (
            _("Order Information"),
            {
                "fields": [
                    "order_date",
                    "priority",
                    "status",
                    "clinical_indication",
                    "notes",
                ]
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]


@admin.register(LabOrderItem)
class LabOrderItemAdmin(admin.ModelAdmin):
    """Admin configuration for LabOrderItem model."""

    list_display = [
        "test_name",
        "lab_order",
        "category",
        "result",
        "is_abnormal",
    ]
    list_filter = [
        "category",
        "is_abnormal",
        "lab_order__clinic",
    ]
    search_fields = [
        "test_name",
        "test_code",
        "lab_order__order_id",
    ]
    ordering = ["lab_order", "id"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["lab_order", "lab_test"]
