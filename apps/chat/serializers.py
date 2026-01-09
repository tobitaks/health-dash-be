from rest_framework import serializers

from apps.utils.sanitization import sanitize_text

from .models import Chat, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("id", "chat", "message_type", "content", "created_at")

    def validate_content(self, value):
        """Sanitize message content to prevent XSS."""
        return sanitize_text(value)


class ChatSerializer(serializers.ModelSerializer):
    """
    Basic serializer for Chats.
    """

    messages = ChatMessageSerializer(many=True)

    class Meta:
        model = Chat
        fields = ("id", "name", "messages")

    def validate_name(self, value):
        """Sanitize chat name to prevent XSS."""
        return sanitize_text(value)
