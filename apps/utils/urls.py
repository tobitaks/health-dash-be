"""URL utilities for generating absolute URLs."""

from django.conf import settings
from django.contrib.sites.models import Site


def absolute_url(url: str) -> str:
    """
    Convert a relative URL to an absolute URL using the site's domain.

    Args:
        url: A relative URL path (e.g., "/api/endpoint/")

    Returns:
        An absolute URL with the full domain (e.g., "https://example.com/api/endpoint/")
    """
    protocol = "https" if getattr(settings, "USE_HTTPS_IN_ABSOLUTE_URLS", False) else "http"
    try:
        domain = Site.objects.get_current().domain
    except Exception:
        # Fallback to localhost if Site is not configured
        domain = "localhost:8000"

    return f"{protocol}://{domain}{url}"
