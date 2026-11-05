"""Google Gemini Text-to-Speech integration module for Page to Voice.

Integrates with the official Google Gen AI Python SDK (google-genai) to generate
high-fidelity audio narration from text chunks using Gemini speech models.
Handles authentication, configurable voice settings, error recovery, rate limiting,
and structured audio file persistence.
"""

from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import find_dotenv, load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

from page_to_voice.narration.models import NarrationChunk
from page_to_voice.tts.audio_writer import save_audio_chunk
from page_to_voice.tts.models import (
    DEFAULT_TTS_MODEL,
    SpeechResult,
    TTSConfig,
    VoiceSettings,
)

logger = logging.getLogger(__name__)

# Ensure local .env variables are reliably loaded across different working directories
_env_file = find_dotenv(usecwd=True)
if not _env_file:
    _candidate = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if _candidate.exists():
        _env_file = str(_candidate)

load_dotenv(_env_file)


def _sanitize_filename(name: str) -> str:
    """Sanitize strings for safe cross-platform filesystem filenames."""
    sanitized = re.sub(r'[\\/*?:"<>| ]', "_", name)
    return sanitized.strip("._")[:40]


class GeminiTTS:
    """Client wrapper for Google Gemini Text-to-Speech generation."""

    def __init__(self, config: Optional[TTSConfig] = None) -> None:
        """Initialize the Gemini TTS client.

        Args:
            config: Optional TTSConfig instance. If omitted, default settings are used.

        Raises:
            ValueError: If no API key is found in config or the GEMINI_API_KEY environment variable.
        """
        self.config = config or TTSConfig()
        self._api_key = self.config.api_key or os.environ.get("GEMINI_API_KEY")

        if not self._api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured. Please supply it via TTSConfig "
                "or set GEMINI_API_KEY in your environment or .env file."
            )

        # Initialize the official Google GenAI client
        self._client = genai.Client(api_key=self._api_key)
        logger.info(
            "Initialized GeminiTTS client (model: %s, voice: %s).",
            self.config.model,
            self.config.voice_settings.voice_name,
        )

    def generate_chunk_audio(
        self,
        chunk: NarrationChunk,
        custom_config: Optional[TTSConfig] = None,
    ) -> SpeechResult:
        """Generate audio for a single narration chunk and persist to disk.

        Args:
            chunk: NarrationChunk object containing text and metadata.
            custom_config: Optional override configuration for this specific chunk.

        Returns:
            SpeechResult with file path, duration, and status metrics.
        """
        cfg = custom_config or self.config
        output_dir = Path(cfg.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build consistent, readable output filename
        file_prefix = f"chunk_{chunk.index:03d}"
        if chunk.chapter_title:
            clean_ch = _sanitize_filename(chunk.chapter_title)
            file_prefix = f"{clean_ch}_{file_prefix}"
        output_path = output_dir / f"{file_prefix}.wav"

        # Check for empty text
        if not chunk.text.strip():
            logger.warning("Chunk %d is empty, skipping TTS generation.", chunk.index)
            return SpeechResult(
                chunk_index=chunk.index,
                status="failed",
                error_message="Chunk text is empty.",
            )

        # Prepare speech config
        speech_config_kwargs: Dict[str, Any] = {}
        if cfg.voice_settings.voice_name:
            speech_config_kwargs["voice_config"] = types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=cfg.voice_settings.voice_name
                )
            )
        if cfg.voice_settings.language_code:
            speech_config_kwargs["language_code"] = cfg.voice_settings.language_code

        gen_config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(**speech_config_kwargs) if speech_config_kwargs else None,
        )

        # Prepare prompt content: incorporate style prompt if specified
        prompt_text = chunk.text
        if cfg.voice_settings.style_prompt:
            prompt_text = f"{cfg.voice_settings.style_prompt}: {chunk.text}"

        attempt = 0
        last_error: Optional[Exception] = None

        while attempt <= cfg.max_retries:
            try:
                logger.debug(
                    "Requesting audio for chunk %d (attempt %d/%d)...",
                    chunk.index,
                    attempt + 1,
                    cfg.max_retries + 1,
                )
                response = self._client.models.generate_content(
                    model=cfg.model,
                    contents=prompt_text,
                    config=gen_config,
                )

                # Extract audio data from the response
                audio_bytes = None
                mime_type = None

                if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.data:
                            audio_bytes = part.inline_data.data
                            mime_type = part.inline_data.mime_type
                            break

                if not audio_bytes:
                    raise ValueError(
                        f"API responded without audio data for chunk {chunk.index}."
                    )

                # Save and validate audio output
                audio_meta = save_audio_chunk(
                    audio_data=audio_bytes,
                    mime_type=mime_type,
                    output_path=output_path,
                    fallback_sample_rate=cfg.sample_rate,
                    channels=cfg.channels,
                    sample_width=cfg.sample_width,
                )

                logger.info(
                    "Successfully generated audio for chunk %d -> %s (duration: %.2fs).",
                    chunk.index,
                    output_path,
                    audio_meta["duration_seconds"],
                )

                return SpeechResult(
                    chunk_index=chunk.index,
                    status="success",
                    audio_path=audio_meta["path"],
                    audio_format="wav",
                    duration_seconds=audio_meta["duration_seconds"],
                    byte_size=audio_meta["byte_size"],
                    sample_rate=audio_meta["sample_rate"],
                    channels=audio_meta["channels"],
                    metadata={
                        "model": cfg.model,
                        "voice": cfg.voice_settings.voice_name,
                        "chapter": chunk.chapter_title,
                        "mime_type": mime_type,
                    },
                )

            except (APIError, Exception) as exc:
                last_error = exc
                attempt += 1
                is_rate_limit = "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc).upper()
                if attempt <= cfg.max_retries:
                    backoff = cfg.retry_delay_seconds * (2 ** (attempt - 1))
                    logger.warning(
                        "Error synthesizing chunk %d (attempt %d): %s. Retrying in %.1fs...",
                        chunk.index,
                        attempt,
                        exc,
                        backoff,
                    )
                    time.sleep(backoff)
                else:
                    logger.error(
                        "Max retries exceeded for chunk %d: %s",
                        chunk.index,
                        exc,
                    )

        # Sanitize error message to ensure no secrets or sensitive data are leaked
        err_msg = str(last_error) if last_error else "Unknown synthesis error."
        return SpeechResult(
            chunk_index=chunk.index,
            status="failed",
            error_message=err_msg,
        )

    def generate_speech_for_chunks(
        self,
        chunks: List[NarrationChunk],
        config: Optional[TTSConfig] = None,
    ) -> List[SpeechResult]:
        """Synthesize audio for a sequence of narration chunks.

        Maintains original chunk ordering and ensures all generated audio files are preserved
        even if a later chunk fails.

        Args:
            chunks: Ordered list of NarrationChunk instances.
            config: Optional TTSConfig override.

        Returns:
            List of SpeechResult objects corresponding to each input chunk.
        """
        results: List[SpeechResult] = []
        cfg = config or self.config

        logger.info("Beginning batch speech generation for %d chunks.", len(chunks))

        for chunk in chunks:
            result = self.generate_chunk_audio(chunk, custom_config=cfg)
            results.append(result)

        successful = sum(1 for r in results if r.status == "success")
        logger.info(
            "Batch speech generation completed: %d/%d succeeded.",
            successful,
            len(chunks),
        )
        return results


def generate_speech_for_chunks(
    chunks: List[NarrationChunk],
    config: Optional[TTSConfig] = None,
) -> List[SpeechResult]:
    """Convenience functional interface to synthesize speech for narration chunks.

    Args:
        chunks: Ordered list of narration chunks.
        config: Optional TTSConfig instance.

    Returns:
        List of SpeechResult objects.
    """
    client = GeminiTTS(config=config)
    return client.generate_speech_for_chunks(chunks=chunks)
