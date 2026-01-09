"""
Input sanitization utilities for user-provided content.

Uses nh3 library to strip malicious HTML/JavaScript while preserving safe content.
"""

import nh3


def sanitize_text(text: str | None, strip_all_html: bool = True) -> str | None:
    """
    Sanitize user input by removing potentially malicious HTML/JavaScript.

    Args:
        text: Raw user input text (can be None)
        strip_all_html: If True, removes ALL HTML tags. If False, allows safe tags.

    Returns:
        Sanitized text with malicious content removed, or None if input was None.

    Examples:
        >>> sanitize_text("<script>alert('xss')</script>Hello")
        'Hello'
        >>> sanitize_text("<b>Bold</b> text", strip_all_html=True)
        'Bold text'
        >>> sanitize_text(None)
        None
    """
    if text is None:
        return None

    if not isinstance(text, str):
        return text

    if not text.strip():
        return text

    if strip_all_html:
        # Remove ALL HTML tags - strictest sanitization
        return nh3.clean(text, tags=set())
    else:
        # Allow basic safe formatting tags
        safe_tags = {"b", "i", "u", "strong", "em", "br", "p"}
        return nh3.clean(text, tags=safe_tags, attributes={})


def sanitize_dict_fields(data: dict, fields: list[str], strip_all_html: bool = True) -> dict:
    """
    Sanitize specific fields in a dictionary.

    Args:
        data: Dictionary containing user input
        fields: List of field names to sanitize
        strip_all_html: If True, removes ALL HTML tags

    Returns:
        Dictionary with specified fields sanitized
    """
    for field in fields:
        if field in data and isinstance(data[field], str):
            data[field] = sanitize_text(data[field], strip_all_html=strip_all_html)
    return data
