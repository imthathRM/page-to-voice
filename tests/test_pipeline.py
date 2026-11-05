"""Unit and integration tests for the complete Page to Voice pipeline."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from page_to_voice.narration.models import Chapter
from page_to_voice.pipeline import process_page_to_voice
from page_to_voice.tts.audio_writer import wrap_pcm_to_wav
from page_to_voice.tts.models import SpeechResult, TTSConfig


class MockTTSClient:
    """Mock TTS client generating local dummy audio files for pipeline verification."""

    def __init__(self, output_dir: Path, synthetic_pcm: bytes) -> None:
        self.output_dir = output_dir
        self.synthetic_pcm = synthetic_pcm

    def generate_speech_for_chunks(self, chunks: list, config: TTSConfig | None = None) -> list[SpeechResult]:
        results = []
        for c in chunks:
            out_file = self.output_dir / f"pipeline_chunk_{c.index:03d}.wav"
            duration, byte_size = wrap_pcm_to_wav(self.synthetic_pcm, out_file)
            results.append(
                SpeechResult(
                    chunk_index=c.index,
                    status="success",
                    audio_path=str(out_file),
                    audio_format="wav",
                    duration_seconds=duration,
                    byte_size=byte_size,
                    sample_rate=24000,
                    channels=1,
                )
            )
        return results


def test_process_page_to_voice_raw_text(
    synthetic_pcm_audio: bytes,
    temp_output_dir: Path,
) -> None:
    """Verify complete pipeline execution: Raw text -> Cleaned -> Chunks -> Audio -> Result."""
    mock_tts = MockTTSClient(temp_output_dir, synthetic_pcm_audio)
    raw_document = (
        "  \x00# Artificial Intelligence in Audio  \n\n\n\n"
        "Page to Voice converts written text into lifelike audiobooks. "
        "It cleans text, prepares narration, and invokes TTS models! "
        "Do you want to listen? Yes, definitely.\n\n"
    )

    result = process_page_to_voice(
        text=raw_document,
        tts_config=TTSConfig(output_dir=temp_output_dir),
        max_chars_per_chunk=100,
        tts_client=mock_tts,
    )

    assert result.success is True
    assert len(result.failed_chunks) == 0
    assert result.cleaned_text.startswith("# Artificial Intelligence in Audio")
    assert result.narration_plan.total_chunks >= 2
    assert len(result.audio_files) == result.narration_plan.total_chunks
    assert result.total_duration_seconds > 0.0
    assert result.total_bytes > 0

    for path_str in result.audio_files:
        assert Path(path_str).exists()


def test_process_page_to_voice_chapters(
    sample_chapters: list[Chapter],
    synthetic_pcm_audio: bytes,
    temp_output_dir: Path,
) -> None:
    """Verify pipeline execution with structured Chapter objects."""
    mock_tts = MockTTSClient(temp_output_dir, synthetic_pcm_audio)

    result = process_page_to_voice(
        chapters=sample_chapters,
        tts_config=TTSConfig(output_dir=temp_output_dir),
        max_chars_per_chunk=80,
        tts_client=mock_tts,
    )

    assert result.success is True
    assert result.narration_plan.total_chunks >= 2
    assert len(result.audio_files) == result.narration_plan.total_chunks


def test_process_page_to_voice_empty_input(temp_output_dir: Path) -> None:
    """Verify pipeline handles empty inputs without errors."""
    mock_tts = MockTTSClient(temp_output_dir, b"")

    result_empty = process_page_to_voice(text="", tts_client=mock_tts)
    assert result_empty.success is True
    assert result_empty.narration_plan.total_chunks == 0
    assert len(result_empty.audio_files) == 0

    result_none = process_page_to_voice(text=None, chapters=None, tts_client=mock_tts)
    assert result_none.success is True
    assert result_none.narration_plan.total_chunks == 0
