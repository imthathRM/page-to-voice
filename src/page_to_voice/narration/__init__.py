"""Narration preparation module for the Page to Voice platform."""

from page_to_voice.narration.boundary_detector import split_sentences
from page_to_voice.narration.chunker import DEFAULT_MAX_CHARS, prepare_narration
from page_to_voice.narration.models import Chapter, NarrationChunk, NarrationPlan

__all__ = [
    "split_sentences",
    "prepare_narration",
    "DEFAULT_MAX_CHARS",
    "NarrationChunk",
    "Chapter",
    "NarrationPlan",
]
