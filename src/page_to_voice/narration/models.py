"""Data models for narration preparation in the Page to Voice platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class NarrationChunk:
    """Represents a speech-ready chunk of narration text.

    Attributes:
        index: Zero-based sequential position of this chunk in the narration.
        text: Speech-ready text string to be sent to the TTS engine.
        character_count: Total Unicode characters in this chunk.
        word_count: Total word count in this chunk.
        estimated_duration_seconds: Estimated audio speech duration in seconds.
        chapter_title: Optional title of the chapter this chunk belongs to.
        section_title: Optional title of the section this chunk belongs to.
        metadata: Optional dictionary for tracking additional context.
    """

    index: int
    text: str
    character_count: int
    word_count: int
    estimated_duration_seconds: float
    chapter_title: Optional[str] = None
    section_title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Chapter:
    """Represents a chapter or major section within a structured document.

    Attributes:
        title: Title or heading of the chapter.
        content: Raw or cleaned text body of the chapter.
        section_title: Optional sub-section title.
        metadata: Optional dictionary for custom chapter attributes.
    """

    title: str
    content: str
    section_title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NarrationPlan:
    """Complete planned narration structure containing all chunks and summary stats.

    Attributes:
        total_chunks: Total number of chunks generated.
        total_characters: Sum of characters across all chunks.
        total_words: Sum of words across all chunks.
        estimated_total_duration_seconds: Sum of estimated speech durations.
        chunks: Ordered list of narration chunks ready for speech synthesis.
        metadata: Optional dictionary for tracking document-level metadata.
    """

    total_chunks: int
    total_characters: int
    total_words: int
    estimated_total_duration_seconds: float
    chunks: List[NarrationChunk] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
