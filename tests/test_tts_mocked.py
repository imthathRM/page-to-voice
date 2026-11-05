"""Unit tests for Gemini TTS with mocked Google GenAI client."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from google.genai.errors import APIError
from page_to_voice.narration.models import NarrationChunk
from page_to_voice.tts.gemini_tts import GeminiTTS, generate_speech_for_chunks
from page_to_voice.tts.models import SpeechResult, TTSConfig, VoiceSettings


def _create_mock_response(audio_bytes: bytes, mime_type: str = "audio/pcm;rate=24000") -> MagicMock:
    """Helper to create a mock Gemini generate_content response."""
    part_mock = MagicMock()
    part_mock.inline_data.data = audio_bytes
    part_mock.inline_data.mime_type = mime_type

    candidate_mock = MagicMock()
    candidate_mock.content.parts = [part_mock]

    response_mock = MagicMock()
    response_mock.candidates = [candidate_mock]
    return response_mock


def test_gemini_tts_init_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that initializing GeminiTTS without an API key raises ValueError."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY is not configured"):
        GeminiTTS(config=TTSConfig(api_key=None))


@patch("page_to_voice.tts.gemini_tts.genai.Client")
def test_gemini_tts_single_chunk_success(
    mock_client_cls: MagicMock,
    synthetic_pcm_audio: bytes,
    temp_output_dir: Path,
) -> None:
    """Verify successful speech generation for a single chunk."""
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _create_mock_response(synthetic_pcm_audio)
    mock_client_cls.return_value = mock_client

    config = TTSConfig(
        api_key="mock-test-key",
        output_dir=temp_output_dir,
        voice_settings=VoiceSettings(voice_name="Kore", language_code="en-US"),
    )
    tts = GeminiTTS(config=config)

    chunk = NarrationChunk(
        index=0,
        text="Hello world, this is a test.",
        character_count=28,
        word_count=6,
        estimated_duration_seconds=2.4,
    )

    result = tts.generate_chunk_audio(chunk)

    assert result.status == "success"
    assert result.chunk_index == 0
    assert result.audio_path is not None
    assert Path(result.audio_path).exists()
    assert result.duration_seconds > 0.1
    assert result.sample_rate == 24000


@patch("page_to_voice.tts.gemini_tts.genai.Client")
def test_gemini_tts_batch_chunks_preserves_order(
    mock_client_cls: MagicMock,
    synthetic_pcm_audio: bytes,
    temp_output_dir: Path,
) -> None:
    """Verify batch speech generation processes chunks in order and writes files."""
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _create_mock_response(synthetic_pcm_audio)
    mock_client_cls.return_value = mock_client

    config = TTSConfig(api_key="mock-test-key", output_dir=temp_output_dir)
    tts = GeminiTTS(config=config)

    chunks = [
        NarrationChunk(index=0, text="First chunk.", character_count=12, word_count=2, estimated_duration_seconds=0.8),
        NarrationChunk(index=1, text="Second chunk.", character_count=13, word_count=2, estimated_duration_seconds=0.8),
    ]

    results = tts.generate_speech_for_chunks(chunks)

    assert len(results) == 2
    assert results[0].chunk_index == 0
    assert results[1].chunk_index == 1
    assert results[0].status == "success"
    assert results[1].status == "success"
    assert Path(results[0].audio_path).exists()
    assert Path(results[1].audio_path).exists()


@patch("page_to_voice.tts.gemini_tts.genai.Client")
@patch("time.sleep", return_value=None)  # Avoid test delay
def test_gemini_tts_retry_on_rate_limit(
    mock_sleep: MagicMock,
    mock_client_cls: MagicMock,
    synthetic_pcm_audio: bytes,
    temp_output_dir: Path,
) -> None:
    """Verify that transient 429 rate limit errors trigger retries and recover."""
    mock_client = MagicMock()
    # First call raises rate limit, second call succeeds
    error_429 = APIError(429, "Resource exhausted (rate limit)")
    mock_client.models.generate_content.side_effect = [
        error_429,
        _create_mock_response(synthetic_pcm_audio),
    ]
    mock_client_cls.return_value = mock_client

    config = TTSConfig(
        api_key="mock-test-key",
        output_dir=temp_output_dir,
        max_retries=2,
        retry_delay_seconds=0.01,
    )
    tts = GeminiTTS(config=config)

    chunk = NarrationChunk(
        index=0,
        text="Retry test.",
        character_count=11,
        word_count=2,
        estimated_duration_seconds=0.8,
    )

    result = tts.generate_chunk_audio(chunk)

    assert result.status == "success"
    assert mock_client.models.generate_content.call_count == 2


@patch("page_to_voice.tts.gemini_tts.genai.Client")
@patch("time.sleep", return_value=None)
def test_gemini_tts_failure_preserves_earlier_chunks(
    mock_sleep: MagicMock,
    mock_client_cls: MagicMock,
    synthetic_pcm_audio: bytes,
    temp_output_dir: Path,
) -> None:
    """Verify that if chunk 2 fails permanently, chunk 1 audio is still saved and intact."""
    mock_client = MagicMock()
    # Chunk 0 succeeds, Chunk 1 fails all retries
    mock_client.models.generate_content.side_effect = [
        _create_mock_response(synthetic_pcm_audio),
        APIError(500, "Internal server error"),
        APIError(500, "Internal server error"),
    ]
    mock_client_cls.return_value = mock_client

    config = TTSConfig(
        api_key="mock-test-key",
        output_dir=temp_output_dir,
        max_retries=1,
        retry_delay_seconds=0.01,
    )
    tts = GeminiTTS(config=config)

    chunks = [
        NarrationChunk(index=0, text="Chunk 0.", character_count=8, word_count=2, estimated_duration_seconds=0.8),
        NarrationChunk(index=1, text="Chunk 1.", character_count=8, word_count=2, estimated_duration_seconds=0.8),
    ]

    results = tts.generate_speech_for_chunks(chunks)

    assert results[0].status == "success"
    assert Path(results[0].audio_path).exists()
    assert results[1].status == "failed"
    assert "Internal server error" in str(results[1].error_message)


def test_gemini_tts_empty_chunk_handling(temp_output_dir: Path) -> None:
    """Verify that empty chunk returns a failed SpeechResult without invoking API."""
    with patch("page_to_voice.tts.gemini_tts.genai.Client"):
        tts = GeminiTTS(config=TTSConfig(api_key="mock-test-key", output_dir=temp_output_dir))
        empty_chunk = NarrationChunk(
            index=0,
            text="   ",
            character_count=3,
            word_count=0,
            estimated_duration_seconds=0.0,
        )
        result = tts.generate_chunk_audio(empty_chunk)
        assert result.status == "failed"
        assert "empty" in result.error_message
