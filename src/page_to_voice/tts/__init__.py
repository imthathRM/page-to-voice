"""Google Gemini Text-to-Speech module for Page to Voice."""

from page_to_voice.tts.audio_writer import (
    AudioFormatError,
    is_wav_format,
    save_audio_chunk,
    wrap_pcm_to_wav,
)
from page_to_voice.tts.gemini_tts import GeminiTTS, generate_speech_for_chunks
from page_to_voice.tts.models import (
    DEFAULT_TTS_MODEL,
    FALLBACK_TTS_MODELS,
    VERIFIED_PREBUILT_VOICES,
    SpeechResult,
    TTSConfig,
    VoiceSettings,
)

__all__ = [
    "GeminiTTS",
    "generate_speech_for_chunks",
    "save_audio_chunk",
    "wrap_pcm_to_wav",
    "is_wav_format",
    "AudioFormatError",
    "SpeechResult",
    "TTSConfig",
    "VoiceSettings",
    "DEFAULT_TTS_MODEL",
    "FALLBACK_TTS_MODELS",
    "VERIFIED_PREBUILT_VOICES",
]
