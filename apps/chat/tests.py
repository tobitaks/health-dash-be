"""
Unit tests for chat serializers.
"""

from django.test import TestCase

from apps.chat.models import Chat, ChatMessage, ChatTypes, MessageTypes
from apps.chat.serializers import ChatMessageSerializer, ChatSerializer
from apps.users.models import CustomUser


class ChatSerializerTestCase(TestCase):
    """Base test case with common fixtures for chat tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.chat = Chat.objects.create(
            user=self.user,
            name="Test Chat",
            chat_type=ChatTypes.CHAT,
        )


class ChatMessageSerializerSanitizationTestCase(ChatSerializerTestCase):
    """Tests for sanitization in ChatMessageSerializer."""

    def test_content_sanitizes_script_tags(self):
        """Script tags in content should be removed."""
        data = {
            "chat": self.chat.id,
            "message_type": MessageTypes.HUMAN,
            "content": "<script>alert('xss')</script>Hello",
        }
        serializer = ChatMessageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["content"], "Hello")

    def test_content_sanitizes_onclick_handlers(self):
        """onclick handlers in content should be removed."""
        data = {
            "chat": self.chat.id,
            "message_type": MessageTypes.HUMAN,
            "content": '<div onclick="evil()">Click me</div>',
        }
        serializer = ChatMessageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("onclick", serializer.validated_data["content"])
        self.assertNotIn("evil", serializer.validated_data["content"])
        self.assertIn("Click me", serializer.validated_data["content"])

    def test_content_sanitizes_javascript_protocol(self):
        """javascript: protocol in links should be removed."""
        data = {
            "chat": self.chat.id,
            "message_type": MessageTypes.HUMAN,
            "content": '<a href="javascript:alert(1)">Click</a>',
        }
        serializer = ChatMessageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("javascript:", serializer.validated_data["content"])

    def test_content_sanitizes_onerror_handlers(self):
        """onerror handlers should be removed."""
        data = {
            "chat": self.chat.id,
            "message_type": MessageTypes.HUMAN,
            "content": '<img src="x" onerror="alert(1)">',
        }
        serializer = ChatMessageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("onerror", serializer.validated_data["content"])
        self.assertNotIn("alert", serializer.validated_data["content"])

    def test_content_removes_html_tags(self):
        """HTML tags in content should be removed."""
        data = {
            "chat": self.chat.id,
            "message_type": MessageTypes.HUMAN,
            "content": "<b>Bold</b> and <i>italic</i> text",
        }
        serializer = ChatMessageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["content"], "Bold and italic text")

    def test_content_preserves_plain_text(self):
        """Plain text content should remain unchanged."""
        data = {
            "chat": self.chat.id,
            "message_type": MessageTypes.HUMAN,
            "content": "Hello, how can I help you today?",
        }
        serializer = ChatMessageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["content"], "Hello, how can I help you today?"
        )

    def test_content_handles_multiline_text(self):
        """Multiline content should be handled correctly."""
        data = {
            "chat": self.chat.id,
            "message_type": MessageTypes.HUMAN,
            "content": "Line 1\nLine 2\nLine 3",
        }
        serializer = ChatMessageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIn("Line 1", serializer.validated_data["content"])
        self.assertIn("Line 2", serializer.validated_data["content"])
        self.assertIn("Line 3", serializer.validated_data["content"])

    def test_content_sanitizes_svg_with_script(self):
        """SVG with embedded scripts should be sanitized."""
        data = {
            "chat": self.chat.id,
            "message_type": MessageTypes.HUMAN,
            "content": '<svg onload="alert(1)">Test</svg>',
        }
        serializer = ChatMessageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("onload", serializer.validated_data["content"])
        self.assertNotIn("alert", serializer.validated_data["content"])


class ChatSerializerSanitizationTestCase(ChatSerializerTestCase):
    """Tests for sanitization in ChatSerializer."""

    def test_name_sanitizes_script_tags(self):
        """Script tags in chat name should be removed."""
        data = {"name": "<script>evil()</script>New Name"}
        serializer = ChatSerializer(self.chat, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["name"], "New Name")

    def test_name_sanitizes_html_tags(self):
        """HTML tags in chat name should be removed."""
        data = {"name": "<b>Bold</b> Chat"}
        serializer = ChatSerializer(self.chat, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["name"], "Bold Chat")

    def test_name_sanitizes_onclick_handlers(self):
        """onclick handlers in chat name should be removed."""
        data = {"name": '<div onclick="evil()">Chat Name</div>'}
        serializer = ChatSerializer(self.chat, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("onclick", serializer.validated_data["name"])
        self.assertIn("Chat Name", serializer.validated_data["name"])

    def test_name_preserves_plain_text(self):
        """Plain text chat name should remain unchanged."""
        data = {"name": "My Conversation About Health"}
        serializer = ChatSerializer(self.chat, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["name"], "My Conversation About Health"
        )

    def test_name_handles_special_characters(self):
        """Special characters in chat name should be preserved."""
        data = {"name": "Q&A Session - 2026"}
        serializer = ChatSerializer(self.chat, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        # The & might be encoded but Q, A, Session, 2026 should be there
        self.assertIn("Q", serializer.validated_data["name"])
        self.assertIn("A", serializer.validated_data["name"])
        self.assertIn("2026", serializer.validated_data["name"])
