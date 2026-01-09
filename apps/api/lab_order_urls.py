"""
URL patterns for Lab Order API.
"""

from django.urls import path

from .lab_order_views import (
    ConsultationLabOrdersView,
    LabOrderDetailView,
    LabOrderItemResultView,
    LabOrderListCreateView,
    LabOrderStatusView,
    LabTestDetailView,
    LabTestListCreateView,
)

app_name = "lab_orders"

urlpatterns = [
    # Lab Test Catalog
    path("tests/", LabTestListCreateView.as_view(), name="test-list-create"),
    path("tests/<int:pk>/", LabTestDetailView.as_view(), name="test-detail"),
    # Lab Orders
    path("", LabOrderListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", LabOrderDetailView.as_view(), name="detail"),
    path("<int:pk>/status/", LabOrderStatusView.as_view(), name="status"),
    path("<int:pk>/items/<int:item_pk>/result/", LabOrderItemResultView.as_view(), name="item-result"),
    # Consultation Lab Orders
    path(
        "consultation/<int:consultation_id>/",
        ConsultationLabOrdersView.as_view(),
        name="consultation-lab-orders",
    ),
]
