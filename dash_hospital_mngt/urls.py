"""Dash Hospital Mngt URL Configuration - REST API Only

This backend serves only REST API endpoints.
Root URL redirects to Swagger API documentation.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [
    # Root redirect to Swagger API docs
    path("", RedirectView.as_view(url="/api/schema/swagger-ui/", permanent=False), name="root"),
    # Django Admin
    path("admin/", admin.site.urls),
    # JWT Authentication endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # Custom Auth API for Vue frontend
    path("api/auth/", include("apps.api.auth_urls")),
    # Clinic API
    path("api/clinic/", include("apps.api.clinic_urls")),
    # Staff API
    path("api/staff/", include("apps.api.staff_urls")),
    # Roles API
    path("api/roles/", include("apps.api.role_urls")),
    # Policies API
    path("api/policies/", include("apps.api.policy_urls")),
    # Services API
    path("api/services/", include("apps.api.service_urls")),
    # Patients API
    path("api/patients/", include("apps.api.patient_urls")),
    # Appointments API
    path("api/appointments/", include("apps.api.appointment_urls")),
    # Consultations API
    path("api/consultations/", include("apps.api.consultation_urls")),
    # Medicines API
    path("api/medicines/", include("apps.api.medicine_urls")),
    # Prescriptions API
    path("api/prescriptions/", include("apps.api.prescription_urls")),
    # Lab Orders API
    path("api/lab-orders/", include("apps.api.lab_order_urls")),
    # Billing/Invoices API
    path("api/invoices/", include("apps.api.billing_urls")),
    # Subscriptions API
    path("api/subscriptions/", include("apps.subscriptions.urls")),
    # Headless auth API (for frontend)
    path("_allauth/", include("allauth.headless.urls")),
    # Celery progress
    path("celery-progress/", include("celery_progress.urls")),
    # API documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Stripe webhooks
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
    # Hijack for impersonation
    path("hijack/", include("hijack.urls", namespace="hijack")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
