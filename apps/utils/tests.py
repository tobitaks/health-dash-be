"""
Unit tests for utility functions.
"""

from django.test import TestCase

from apps.utils.sanitization import sanitize_dict_fields, sanitize_text


class SanitizeTextTestCase(TestCase):
    """Tests for the sanitize_text function."""

    def test_removes_script_tags(self):
        """Script tags should be completely removed."""
        malicious = "<script>alert('xss')</script>Hello World"
        result = sanitize_text(malicious)
        self.assertEqual(result, "Hello World")
        self.assertNotIn("<script>", result)
        self.assertNotIn("alert", result)

    def test_removes_script_tags_with_attributes(self):
        """Script tags with attributes should be removed."""
        malicious = '<script src="evil.js"></script>Safe content'
        result = sanitize_text(malicious)
        self.assertEqual(result, "Safe content")

    def test_removes_onclick_handlers(self):
        """Event handlers like onclick should be removed."""
        malicious = '<div onclick="evil()">Click me</div>'
        result = sanitize_text(malicious)
        self.assertNotIn("onclick", result)
        self.assertNotIn("evil", result)
        self.assertIn("Click me", result)

    def test_removes_onerror_handlers(self):
        """Event handlers like onerror should be removed."""
        malicious = '<img src="x" onerror="alert(1)">'
        result = sanitize_text(malicious)
        self.assertNotIn("onerror", result)
        self.assertNotIn("alert", result)

    def test_removes_javascript_protocol(self):
        """javascript: protocol in links should be removed."""
        malicious = '<a href="javascript:alert(1)">Click</a>'
        result = sanitize_text(malicious)
        self.assertNotIn("javascript:", result)

    def test_removes_all_html_tags_by_default(self):
        """All HTML tags should be stripped by default."""
        html = "<b>Bold</b> and <i>italic</i> text"
        result = sanitize_text(html)
        self.assertEqual(result, "Bold and italic text")
        self.assertNotIn("<b>", result)
        self.assertNotIn("<i>", result)

    def test_preserves_plain_text(self):
        """Plain text without HTML should be unchanged."""
        plain = "This is plain text with no HTML"
        result = sanitize_text(plain)
        self.assertEqual(result, plain)

    def test_handles_none_value(self):
        """None input should return None."""
        result = sanitize_text(None)
        self.assertIsNone(result)

    def test_handles_empty_string(self):
        """Empty string should return empty string."""
        result = sanitize_text("")
        self.assertEqual(result, "")

    def test_handles_whitespace_only(self):
        """Whitespace-only string should be preserved."""
        result = sanitize_text("   ")
        self.assertEqual(result, "   ")

    def test_handles_non_string_input(self):
        """Non-string input should be returned as-is."""
        result = sanitize_text(123)
        self.assertEqual(result, 123)

    def test_removes_svg_with_script(self):
        """SVG elements with embedded scripts should be sanitized."""
        malicious = '<svg onload="alert(1)"><circle r="50"/></svg>'
        result = sanitize_text(malicious)
        self.assertNotIn("onload", result)
        self.assertNotIn("alert", result)

    def test_multiline_content(self):
        """Multiline content should be handled correctly."""
        text = """Line 1
        <script>evil()</script>
        Line 2"""
        result = sanitize_text(text)
        self.assertIn("Line 1", result)
        self.assertIn("Line 2", result)
        self.assertNotIn("<script>", result)


class SanitizeDictFieldsTestCase(TestCase):
    """Tests for the sanitize_dict_fields function."""

    def test_sanitizes_specified_fields(self):
        """Only specified fields should be sanitized."""
        data = {
            "name": "<script>alert(1)</script>John",
            "age": 30,
            "bio": "<b>Bold</b> text",
        }
        result = sanitize_dict_fields(data, ["name", "bio"])
        self.assertEqual(result["name"], "John")
        self.assertEqual(result["bio"], "Bold text")
        self.assertEqual(result["age"], 30)

    def test_ignores_missing_fields(self):
        """Missing fields should not cause errors."""
        data = {"name": "John"}
        result = sanitize_dict_fields(data, ["name", "missing_field"])
        self.assertEqual(result["name"], "John")
        self.assertNotIn("missing_field", result)

    def test_ignores_non_string_fields(self):
        """Non-string fields should be left unchanged."""
        data = {
            "name": "<script>alert(1)</script>John",
            "count": 42,
            "active": True,
        }
        result = sanitize_dict_fields(data, ["name", "count", "active"])
        self.assertEqual(result["name"], "John")
        self.assertEqual(result["count"], 42)
        self.assertTrue(result["active"])

    def test_empty_fields_list(self):
        """Empty fields list should return data unchanged."""
        data = {"name": "<b>John</b>"}
        result = sanitize_dict_fields(data, [])
        self.assertEqual(result["name"], "<b>John</b>")

    def test_modifies_original_dict(self):
        """The function modifies the original dict (in-place)."""
        data = {"name": "<script>x</script>John"}
        result = sanitize_dict_fields(data, ["name"])
        self.assertEqual(data["name"], "John")
        self.assertIs(result, data)
