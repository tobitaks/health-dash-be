"""
URL patterns for Invoice/Billing API.
"""

from django.urls import path

from .billing_views import (
    InvoiceListCreateView,
    InvoiceDetailView,
    ConsultationInvoiceView,
    InvoicePayView,
    InvoiceFinalizeView,
    InvoiceCancelView,
)

app_name = "billing"

urlpatterns = [
    path("", InvoiceListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", InvoiceDetailView.as_view(), name="detail"),
    path("<int:pk>/pay/", InvoicePayView.as_view(), name="pay"),
    path("<int:pk>/finalize/", InvoiceFinalizeView.as_view(), name="finalize"),
    path("<int:pk>/cancel/", InvoiceCancelView.as_view(), name="cancel"),
    path(
        "consultation/<int:consultation_id>/",
        ConsultationInvoiceView.as_view(),
        name="consultation-invoice",
    ),
]
