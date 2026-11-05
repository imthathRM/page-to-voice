"""Unit tests for the Audio Writer and WAV packaging module."""

from __future__ import annotations

import wave
from pathlib import Path
import pytest

from page_to_voice.tts.audio_writer import (
    AudioFormatError,
    is_wav_format,
    parse_sample_rate_from_mime,
    save_audio_chunk,
    validate_wav_bytes,
    wrap_pcm_to_wav,
)


def test_is_wav_format_detection(synthetic_pcm_audio: bytes, temp_output_dir: Path) -> None:
    """Verify is_wav_format accurately distinguishes between raw PCM and RIFF/WAV data."""
    # Raw PCM should return False
    assert not is_wav_format(synthetic_pcm_audio)
    assert not is_wav_format(b"short")

    # Wrap into real WAV first
    wav_path = temp_output_dir / "valid.wav"
    wrap_pcm_to_wav(synthetic_pcm_audio, wav_path, sample_rate=24000)
    wav_bytes = wav_path.read_bytes()

    assert is_wav_format(wav_bytes)


def test_parse_sample_rate_from_mime() -> None:
    """Verify sample rate parsing from various MIME type strings."""
    assert parse_sample_rate_from_mime("audio/pcm;rate=24000") == 24000
    assert parse_sample_rate_from_mime("audio/pcm; rate=16000") == 16000
    assert parse_sample_rate_from_mime("audio/wav", fallback_rate=24000) == 24000
    assert parse_sample_rate_from_mime(None, fallback_rate=22050) == 22050
    assert parse_sample_rate_from_mime("audio/pcm;rate=invalid", fallback_rate=24000) == 24000


def test_wrap_pcm_to_wav_playable(synthetic_pcm_audio: bytes, temp_output_dir: Path) -> None:
    """Verify that wrapped PCM data results in a playable, standard WAV file."""
    output_file = temp_output_dir / "test_wrap.wav"
    duration, file_size = wrap_pcm_to_wav(
        pcm_data=synthetic_pcm_audio,
        output_path=output_file,
        sample_rate=24000,
        channels=1,
        sample_width=2,
    )

    assert output_file.exists()
    assert file_size > len(synthetic_pcm_audio)  # RIFF header overhead
    assert duration > 0.15

    # Verify using standard library wave module
    with wave.open(str(output_file), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 24000
        assert wf.getnframes() > 0


def test_save_audio_chunk_handles_pcm(synthetic_pcm_audio: bytes, temp_output_dir: Path) -> None:
    """Verify save_audio_chunk correctly packages raw PCM when MIME is audio/pcm."""
    out_file = temp_output_dir / "saved_pcm.wav"
    meta = save_audio_chunk(
        audio_data=synthetic_pcm_audio,
        mime_type="audio/pcm;rate=24000",
        output_path=out_file,
    )

    assert out_file.exists()
    assert meta["sample_rate"] == 24000
    assert meta["channels"] == 1
    assert meta["duration_seconds"] > 0.0


def test_save_audio_chunk_handles_existing_wav(synthetic_pcm_audio: bytes, temp_output_dir: Path) -> None:
    """Verify save_audio_chunk validates and writes data that already possesses a RIFF container."""
    initial_wav = temp_output_dir / "initial.wav"
    wrap_pcm_to_wav(synthetic_pcm_audio, initial_wav, sample_rate=24000)
    wav_bytes = initial_wav.read_bytes()

    out_file = temp_output_dir / "saved_wav.wav"
    meta = save_audio_chunk(
        audio_data=wav_bytes,
        mime_type="audio/wav",
        output_path=out_file,
    )

    assert out_file.exists()
    assert meta["sample_rate"] == 24000
    assert meta["duration_seconds"] > 0.0


def test_validate_wav_bytes_raises_on_invalid() -> None:
    """Ensure invalid or corrupt WAV headers raise AudioFormatError."""
    with pytest.raises(AudioFormatError, match="too short"):
        validate_wav_bytes(b"RIFFshort")

    with pytest.raises(AudioFormatError, match="Missing RIFF/WAVE container signature"):
        validate_wav_bytes(b"RIFF" + b"\x00" * 4 + b"JPEG" + b"\x00" * 32)


def test_empty_audio_raises_error(temp_output_dir: Path) -> None:
    """Ensure empty audio bytes raise AudioFormatError."""
    with pytest.raises(AudioFormatError, match="empty"):
        save_audio_chunk(
            audio_data=b"",
            mime_type="audio/pcm",
            output_path=temp_output_dir / "empty.wav",
        )
