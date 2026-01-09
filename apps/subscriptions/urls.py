from django.urls import path

from . import views

app_name = "subscriptions"

# API-only subscription routes (template views removed)
urlpatterns = [
    # Product listing API
    path("api/active-products/", views.ProductWithMetadataAPI.as_view(), name="products_api"),
    # Stripe API views that return Stripe URLs (for frontend integration)
    path(
        "stripe/api/create-checkout-session/",
        views.CreateCheckoutSession.as_view(),
        name="api_create_checkout_session",
    ),
    path("stripe/api/create-portal-session/", views.CreatePortalSession.as_view(), name="api_create_portal_session"),
]
