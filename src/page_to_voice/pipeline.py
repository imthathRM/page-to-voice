"""End-to-end processing pipeline for Page to Voice.

Coordinates the end-to-end workflow:
Raw Extracted Text -> Text Cleaning -> Narration Preparation -> Gemini TTS -> Audio Persistence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from page_to_voice.cleaning.text_cleaner import clean_text
from page_to_voice.narration.chunker import DEFAULT_MAX_CHARS, prepare_narration
from page_to_voice.narration.models import Chapter, NarrationPlan
from page_to_voice.tts.gemini_tts import GeminiTTS
from page_to_voice.tts.models import SpeechResult, TTSConfig

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Structured end-to-end result of processing a document through the Page to Voice pipeline.

    Attributes:
        cleaned_text: Normalized and cleaned text representation.
        narration_plan: Speech-ready structured narration plan with all chunks.
        speech_results: List of SpeechResult instances for each synthesized chunk.
        audio_files: Ordered list of successfully written audio file paths.
        total_duration_seconds: Total speech duration of all generated audio in seconds.
        total_bytes: Total size on disk of all generated audio files in bytes.
        success: True if all chunks were successfully converted to speech.
        failed_chunks: List of chunk indices that encountered synthesis failures.
        metadata: Optional dictionary with process metadata and parameters.
    """

    cleaned_text: str
    narration_plan: NarrationPlan
    speech_results: List[SpeechResult] = field(default_factory=list)
    audio_files: List[str] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    total_bytes: int = 0
    success: bool = True
    failed_chunks: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


def process_page_to_voice(
    text: Optional[str] = None,
    chapters: Optional[List[Chapter]] = None,
    tts_config: Optional[TTSConfig] = None,
    max_chars_per_chunk: int = DEFAULT_MAX_CHARS,
    tts_client: Optional[Any] = None,
) -> PipelineResult:
    """Execute the complete Page to Voice processing pipeline.

    Takes raw extracted document text or structured chapters, cleans and normalizes the text,
    splits and batches into speech-ready narration chunks, generates speech via Gemini TTS,
    and returns a structured PipelineResult containing all audio paths and metrics.

    Args:
        text: Raw document text string. Optional if chapters are supplied.
        chapters: Optional list of structured Chapter objects.
        tts_config: Optional TTSConfig for voice, model, and directory configuration.
        max_chars_per_chunk: Maximum characters allowed per narration chunk.
        tts_client: Optional pre-configured TTS client (useful for dependency injection or testing).

    Returns:
        PipelineResult with all metrics, cleaned text, and audio paths.
    """
    logger.info("Initiating Page to Voice processing pipeline.")

    cfg = tts_config or TTSConfig()

    # Step 1 & 2: Text Cleaning and Narration Preparation
    if chapters:
        # Multiple chapters
        narration_plan = prepare_narration(
            chapters=chapters,
            max_chars=max_chars_per_chunk,
            auto_clean=True,
        )
        cleaned_full_text = "\n\n".join(c.content for c in chapters)
    elif text is not None:
        cleaned_full_text = clean_text(text)
        narration_plan = prepare_narration(
            text=cleaned_full_text,
            max_chars=max_chars_per_chunk,
            auto_clean=False,  # Already cleaned above
        )
    else:
        logger.warning("process_page_to_voice received neither text nor chapters.")
        empty_plan = NarrationPlan(
            total_chunks=0,
            total_characters=0,
            total_words=0,
            estimated_total_duration_seconds=0.0,
            chunks=[],
        )
        return PipelineResult(
            cleaned_text="",
            narration_plan=empty_plan,
            speech_results=[],
            audio_files=[],
            total_duration_seconds=0.0,
            total_bytes=0,
            success=True,
        )

    # If there are no chunks to synthesize
    if not narration_plan.chunks:
        return PipelineResult(
            cleaned_text=cleaned_full_text,
            narration_plan=narration_plan,
            speech_results=[],
            audio_files=[],
            total_duration_seconds=0.0,
            total_bytes=0,
            success=True,
        )

    # Step 3: Speech Generation via Gemini TTS
    if tts_client is None:
        tts_client = GeminiTTS(config=cfg)

    speech_results = tts_client.generate_speech_for_chunks(
        chunks=narration_plan.chunks,
        config=cfg,
    )

    audio_files: List[str] = []
    failed_chunks: List[int] = []
    total_duration = 0.0
    total_bytes = 0

    for res in speech_results:
        if res.status == "success" and res.audio_path:
            audio_files.append(res.audio_path)
            total_duration += res.duration_seconds
            total_bytes += res.byte_size
        else:
            failed_chunks.append(res.chunk_index)

    overall_success = len(failed_chunks) == 0

    logger.info(
        "Pipeline finished: %d audio files generated (%.2fs total, %d bytes, success=%s).",
        len(audio_files),
        total_duration,
        total_bytes,
        overall_success,
    )

    return PipelineResult(
        cleaned_text=cleaned_full_text,
        narration_plan=narration_plan,
        speech_results=speech_results,
        audio_files=audio_files,
        total_duration_seconds=round(total_duration, 2),
        total_bytes=total_bytes,
        success=overall_success,
        failed_chunks=failed_chunks,
        metadata={
            "model": cfg.model,
            "voice": cfg.voice_settings.voice_name,
            "total_chunks": narration_plan.total_chunks,
        },
    )
