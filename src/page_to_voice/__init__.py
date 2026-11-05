"""Page to Voice: Intelligent Audiobook Generation and Listening Platform.

Core processing modules:
1. Text Cleaning: Multi-lingual Unicode text normalization, structure & math preservation.
2. Narration Preparation: Sentence boundary detection, configurable chunking, chapter support.
3. Google Gemini TTS: High-fidelity speech synthesis, PCM/WAV audio packaging.
4. Pipeline: End-to-end integration orchestrator.
"""

from page_to_voice.cleaning import clean_text
from page_to_voice.narration import (
    DEFAULT_MAX_CHARS,
    Chapter,
    NarrationChunk,
    NarrationPlan,
    prepare_narration,
    split_sentences,
)
from page_to_voice.pipeline import PipelineResult, process_page_to_voice
from page_to_voice.tts import (
    DEFAULT_TTS_MODEL,
    FALLBACK_TTS_MODELS,
    VERIFIED_PREBUILT_VOICES,
    AudioFormatError,
    GeminiTTS,
    SpeechResult,
    TTSConfig,
    VoiceSettings,
    generate_speech_for_chunks,
    is_wav_format,
    save_audio_chunk,
    wrap_pcm_to_wav,
)

__all__ = [
    # Cleaning
    "clean_text",
    # Narration
    "split_sentences",
    "prepare_narration",
    "DEFAULT_MAX_CHARS",
    "NarrationChunk",
    "Chapter",
    "NarrationPlan",
    # TTS
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
    # Pipeline
    "process_page_to_voice",
    "PipelineResult",
]
