"""Live Google Gemini TTS integration tests.

These tests execute real API calls against the Google Gemini TTS service.
They are automatically skipped if the GEMINI_API_KEY environment variable
is not set, is empty, or contains a placeholder value.
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest

from dotenv import find_dotenv, load_dotenv
from page_to_voice.narration.models import NarrationChunk
from page_to_voice.tts.gemini_tts import GeminiTTS
from page_to_voice.tts.models import TTSConfig, VoiceSettings

# Ensure .env is located reliably whether pytest is run from root or subdirectories
_env_path = find_dotenv(usecwd=True)
if not _env_path:
    _candidate = Path(__file__).resolve().parent.parent / ".env"
    if _candidate.exists():
        _env_path = str(_candidate)

load_dotenv(_env_path, override=True)

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
_PLACEHOLDER_PREFIXES = ("your_", "your-", "placeholder", "changeme", "xxx", "todo")
HAS_VALID_KEY = bool(
    API_KEY
    and not any(API_KEY.lower().startswith(p) for p in _PLACEHOLDER_PREFIXES)
    and len(API_KEY) > 10
)


@pytest.mark.skipif(
    not HAS_VALID_KEY,
    reason="GEMINI_API_KEY is not set or contains a placeholder. Live API test skipped.",
)
def test_live_tts_english(temp_output_dir: Path) -> None:
    """Live API test: English text speech generation."""
    config = TTSConfig(
        api_key=API_KEY,
        output_dir=temp_output_dir,
        voice_settings=VoiceSettings(voice_name="Kore", language_code="en-US"),
    )
    tts = GeminiTTS(config=config)
    chunk = NarrationChunk(
        index=0,
        text="Hello! Welcome to the Page to Voice audiobook generator.",
        character_count=57,
        word_count=9,
        estimated_duration_seconds=3.6,
    )
    result = tts.generate_chunk_audio(chunk)

    assert result.status == "success", f"Live TTS failed: {result.error_message}"
    assert result.audio_path is not None
    assert Path(result.audio_path).exists()
    assert result.duration_seconds > 0.5


@pytest.mark.skipif(
    not HAS_VALID_KEY,
    reason="GEMINI_API_KEY is not set or contains a placeholder. Live API test skipped.",
)
def test_live_tts_tamil(temp_output_dir: Path) -> None:
    """Live API test: Tamil text speech generation."""
    config = TTSConfig(
        api_key=API_KEY,
        output_dir=temp_output_dir,
        voice_settings=VoiceSettings(voice_name="Kore", language_code="ta-IN"),
    )
    tts = GeminiTTS(config=config)
    chunk = NarrationChunk(
        index=0,
        text="வணக்கம், இது தமிழ் ஆடியோ புத்தகம் தயாரிக்கும் சோதனை.",
        character_count=54,
        word_count=7,
        estimated_duration_seconds=3.0,
    )
    result = tts.generate_chunk_audio(chunk)

    assert result.status == "success", f"Live Tamil TTS failed: {result.error_message}"
    assert result.audio_path is not None
    assert Path(result.audio_path).exists()


@pytest.mark.skipif(
    not HAS_VALID_KEY,
    reason="GEMINI_API_KEY is not set or contains a placeholder. Live API test skipped.",
)
def test_live_tts_sinhala(temp_output_dir: Path) -> None:
    """Live API test: Sinhala text speech generation."""
    config = TTSConfig(
        api_key=API_KEY,
        output_dir=temp_output_dir,
        voice_settings=VoiceSettings(voice_name="Kore", language_code="si-LK"),
    )
    tts = GeminiTTS(config=config)
    chunk = NarrationChunk(
        index=0,
        text="ආයුබෝවන්, මෙය සිංහල ශ්‍රව්‍ය පොත් නිර්මාණය කිරීමේ පරීක්ෂණයකි.",
        character_count=60,
        word_count=7,
        estimated_duration_seconds=3.0,
    )
    result = tts.generate_chunk_audio(chunk)

    assert result.status == "success", f"Live Sinhala TTS failed: {result.error_message}"
    assert result.audio_path is not None
    assert Path(result.audio_path).exists()
