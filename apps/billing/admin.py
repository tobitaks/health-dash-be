from django.contrib import admin

from apps.billing.models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ["description", "quantity", "unit_price", "amount", "service"]
    readonly_fields = ["amount"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_id",
        "patient",
        "invoice_date",
        "status",
        "total",
        "amount_paid",
        "item_count",
        "created_by",
    ]
    list_filter = ["status", "invoice_date", "clinic"]
    search_fields = ["invoice_id", "patient__first_name", "patient__last_name"]
    ordering = ["-invoice_date", "-created_at"]
    inlines = [InvoiceItemInline]
    readonly_fields = ["subtotal", "discount_amount", "total", "balance"]


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ["invoice", "description", "quantity", "unit_price", "amount"]
    list_filter = ["invoice__clinic"]
    search_fields = ["description", "invoice__invoice_id"]
