"""
Speech-to-text for dictated chief complaints via LiteLLM (OpenAI transcription models).
"""

import logging

import litellm
from django.conf import settings

logger = logging.getLogger(__name__)

# OpenAI transcription endpoints cap uploads at 25 MB.
MAX_AUDIO_BYTES = 25 * 1024 * 1024

TRANSCRIPTION_PROMPT = "Medical chief complaint dictated by a physician during a clinic consultation."


def transcribe_audio(fileobj, filename: str, content_type: str) -> str:
    """
    Transcribe an uploaded audio file to English text.

    Audio is streamed straight to the provider; nothing is persisted locally.
    """
    response = litellm.transcription(
        model=settings.TRANSCRIPTION_MODEL,
        file=(filename, fileobj, content_type),
        language="en",
        prompt=TRANSCRIPTION_PROMPT,
        api_key=settings.OPENAI_API_KEY,
    )
    return (response.text or "").strip()
