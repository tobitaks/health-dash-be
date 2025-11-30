"""
URL patterns for role management API.
"""

from django.urls import path

from .role_views import (
    PolicyListView,
    RoleDetailView,
    RoleListCreateView,
    UserRoleDetailView,
    UserRoleListView,
)

app_name = "roles"

urlpatterns = [
    # Role CRUD
    path("", RoleListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", RoleDetailView.as_view(), name="detail"),
    # User role assignments
    path("users/<int:user_id>/", UserRoleListView.as_view(), name="user-roles"),
    path("users/<int:user_id>/<int:role_id>/", UserRoleDetailView.as_view(), name="user-role-detail"),
]
