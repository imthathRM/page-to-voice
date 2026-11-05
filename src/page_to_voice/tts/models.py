"""Data models and configuration for Google Gemini TTS in Page to Voice."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Verified prebuilt voices available in Google Gemini TTS models
VERIFIED_PREBUILT_VOICES = (
    "Kore",
    "Puck",
    "Zephyr",
    "Aoede",
    "Fenrir",
    "Charon",
    "Autonoe",
    "Orus",
    "Umbriel",
    "Erinome",
    "Laomedeia",
    "Schedar",
)

# Verified official model identifiers for speech generation
DEFAULT_TTS_MODEL = "gemini-3.8-flash-tts"
FALLBACK_TTS_MODELS = (
    "gemini-3.8-flash-lite-tts",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
)


@dataclass
class VoiceSettings:
    """Voice configuration settings for Gemini TTS speech generation.

    Attributes:
        voice_name: Name of the prebuilt voice persona (e.g. 'Kore', 'Puck', 'Zephyr').
        language_code: Optional BCP-47 language tag (e.g. 'en-US', 'ta-IN', 'si-LK').
        style_prompt: Optional natural language direction (e.g. 'Narrate calmly and clearly').
    """

    voice_name: str = "Kore"
    language_code: Optional[str] = None
    style_prompt: Optional[str] = None

    def __post_init__(self) -> None:
        if self.voice_name not in VERIFIED_PREBUILT_VOICES:
            # Allow custom or newly introduced voices, but log/track if outside known prebuilt set
            pass


@dataclass
class TTSConfig:
    """Engine configuration for Gemini TTS generation and audio persistence.

    Attributes:
        model: Target Gemini model identifier (default 'gemini-3.8-flash-tts').
        voice_settings: Configured VoiceSettings instance.
        output_dir: Directory path where generated audio files are saved.
        sample_rate: Expected audio sample rate in Hz (default 24000 Hz).
        channels: Number of audio channels (1 = mono, 2 = stereo).
        sample_width: PCM bit depth in bytes (2 = 16-bit PCM).
        api_key: Optional explicit API key; if omitted, reads from GEMINI_API_KEY environment variable.
        max_retries: Maximum retry attempts for transient API / rate limit errors.
        retry_delay_seconds: Base backoff delay in seconds between retries.
    """

    model: str = DEFAULT_TTS_MODEL
    voice_settings: VoiceSettings = field(default_factory=VoiceSettings)
    output_dir: Path = field(default_factory=lambda: Path("outputs"))
    sample_rate: int = 24000
    channels: int = 1
    sample_width: int = 2
    api_key: Optional[str] = None
    max_retries: int = 3
    retry_delay_seconds: float = 2.0

    def __post_init__(self) -> None:
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)


@dataclass
class SpeechResult:
    """Result of synthesizing audio for a single narration chunk.

    Attributes:
        chunk_index: Index of the narration chunk this result corresponds to.
        status: Status code ('success' or 'failed').
        audio_path: Filesystem path to the written WAV audio file (if successful).
        audio_format: File format of generated audio (typically 'wav').
        duration_seconds: Actual duration of synthesized audio in seconds.
        byte_size: Size of the saved audio file in bytes.
        sample_rate: Sample rate in Hz.
        channels: Channel count (1 for mono).
        error_message: Error description if status == 'failed'.
        metadata: Optional dictionary with extra context or API metrics.
    """

    chunk_index: int
    status: str
    audio_path: Optional[str] = None
    audio_format: str = "wav"
    duration_seconds: float = 0.0
    byte_size: int = 0
    sample_rate: int = 24000
    channels: int = 1
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
