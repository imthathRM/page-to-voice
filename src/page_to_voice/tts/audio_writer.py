"""Audio formatting and WAV packaging module for Page to Voice.

Handles inspection and conversion of TTS audio bytes. If raw PCM data is returned,
it formats and packages it into a standard, fully playable RIFF/WAV audio container.
If a WAV container is returned, it validates the RIFF/WAVE headers before saving.
"""

from __future__ import annotations

import logging
import re
import struct
import wave
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Standard RIFF header magic constants
RIFF_MAGIC = b"RIFF"
WAVE_MAGIC = b"WAVE"
FMT_MAGIC = b"fmt "

_RATE_REGEX = re.compile(r"rate=(\d+)", re.IGNORECASE)


class AudioFormatError(ValueError):
    """Raised when audio data fails validation or cannot be formatted into WAV."""


def is_wav_format(data: bytes) -> bool:
    """Check if byte data begins with a valid RIFF/WAVE header structure."""
    if len(data) < 44:
        return False
    return data[:4] == RIFF_MAGIC and data[8:12] == WAVE_MAGIC


def parse_sample_rate_from_mime(mime_type: Optional[str], fallback_rate: int = 24000) -> int:
    """Extract sample rate integer from MIME type string if present."""
    if not mime_type:
        return fallback_rate
    match = _RATE_REGEX.search(mime_type)
    if match:
        try:
            parsed = int(match.group(1))
            if 8000 <= parsed <= 96000:
                return parsed
        except ValueError:
            pass
    return fallback_rate


def validate_wav_bytes(wav_data: bytes) -> Tuple[int, int, int]:
    """Validate that WAV byte data contains valid RIFF/WAVE structure and readable chunks.

    Returns:
        Tuple of (channels, sample_rate, sample_width_bytes).

    Raises:
        AudioFormatError: If the byte data is malformed or invalid.
    """
    if len(wav_data) < 44:
        raise AudioFormatError(f"WAV byte sequence too short ({len(wav_data)} bytes, expected >= 44).")

    if wav_data[:4] != RIFF_MAGIC or wav_data[8:12] != WAVE_MAGIC:
        raise AudioFormatError("Missing RIFF/WAVE container signature.")

    # Find the 'fmt ' chunk
    pos = 12
    fmt_found = False
    channels = 1
    sample_rate = 24000
    sample_width = 2

    data_len = len(wav_data)
    while pos + 8 <= data_len:
        chunk_id = wav_data[pos : pos + 4]
        chunk_size = struct.unpack("<I", wav_data[pos + 4 : pos + 8])[0]
        pos += 8

        if chunk_id == FMT_MAGIC and chunk_size >= 16:
            fmt_found = True
            audio_fmt, n_channels, s_rate, byte_rate, block_align, bits_per_sample = struct.unpack(
                "<HHIIHH", wav_data[pos : pos + 16]
            )
            channels = n_channels
            sample_rate = s_rate
            sample_width = bits_per_sample // 8
            break

        pos += chunk_size

    if not fmt_found:
        raise AudioFormatError("No valid 'fmt ' chunk found inside WAV container.")

    return channels, sample_rate, sample_width


def wrap_pcm_to_wav(
    pcm_data: bytes,
    output_path: Path,
    sample_rate: int = 24000,
    channels: int = 1,
    sample_width: int = 2,
) -> Tuple[float, int]:
    """Convert raw PCM audio bytes into a standard playable WAV file with valid headers.

    Args:
        pcm_data: Raw PCM audio sample bytes (little-endian).
        output_path: Path where the .wav file should be written.
        sample_rate: Sampling frequency in Hz (default 24000).
        channels: Channel count (1 for mono, 2 for stereo).
        sample_width: Bytes per sample (2 for 16-bit PCM).

    Returns:
        Tuple of (duration_seconds, total_file_size_bytes).

    Raises:
        AudioFormatError: If PCM data is empty or writing fails.
    """
    if not pcm_data:
        raise AudioFormatError("Cannot wrap empty PCM byte array into WAV.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)
    except Exception as exc:
        raise AudioFormatError(f"Failed to write PCM data into WAV file: {exc}") from exc

    # Validate resulting file can be parsed by wave standard library
    try:
        with wave.open(str(output_path), "rb") as verify_wav:
            n_frames = verify_wav.getnframes()
            f_rate = verify_wav.getframerate()
            duration = round(n_frames / float(f_rate), 2)
    except Exception as exc:
        raise AudioFormatError(f"Generated WAV file failed validation: {exc}") from exc

    file_size = output_path.stat().st_size
    logger.debug(
        "Wrapped PCM to WAV successfully at %s (size: %d bytes, duration: %.2fs).",
        output_path,
        file_size,
        duration,
    )
    return duration, file_size


def save_audio_chunk(
    audio_data: bytes,
    mime_type: Optional[str],
    output_path: Path,
    fallback_sample_rate: int = 24000,
    channels: int = 1,
    sample_width: int = 2,
) -> Dict[str, Any]:
    """Save raw audio data (PCM or WAV) to a verified, playable .wav file.

    Inspects byte payload and MIME type:
    - If already standard WAV, validates RIFF structure and writes to disk.
    - If raw PCM, synthesizes standard RIFF/WAV headers and writes frames.

    Args:
        audio_data: Audio bytes returned from TTS API.
        mime_type: MIME type string reported by TTS API (e.g. 'audio/wav', 'audio/pcm;rate=24000').
        output_path: Path where the output file should be saved.
        fallback_sample_rate: Sample rate to use if not specified in MIME or WAV header.
        channels: Channel count (default 1).
        sample_width: Bytes per sample (default 2).

    Returns:
        Dictionary containing metadata: path, duration_seconds, byte_size, sample_rate, channels.
    """
    if not audio_data:
        raise AudioFormatError("Received empty audio data from TTS service.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if is_wav_format(audio_data):
        # Already has WAV container; validate before saving
        ch, rate, width = validate_wav_bytes(audio_data)
        output_path.write_bytes(audio_data)

        with wave.open(str(output_path), "rb") as verify_wav:
            n_frames = verify_wav.getnframes()
            duration = round(n_frames / float(rate), 2)
        byte_size = output_path.stat().st_size

        return {
            "path": str(output_path),
            "duration_seconds": duration,
            "byte_size": byte_size,
            "sample_rate": rate,
            "channels": ch,
            "sample_width": width,
        }

    # Otherwise, data is raw PCM (e.g. audio/pcm, audio/l16)
    rate = parse_sample_rate_from_mime(mime_type, fallback_rate=fallback_sample_rate)
    duration, byte_size = wrap_pcm_to_wav(
        pcm_data=audio_data,
        output_path=output_path,
        sample_rate=rate,
        channels=channels,
        sample_width=sample_width,
    )

    return {
        "path": str(output_path),
        "duration_seconds": duration,
        "byte_size": byte_size,
        "sample_rate": rate,
        "channels": channels,
        "sample_width": sample_width,
    }
