"""Text cleaning module for Page to Voice.

Provides robust, multi-language Unicode text cleaning suitable for preparation
for text-to-speech audio synthesis. Preserves document structure, headings,
paragraphs, mathematical expressions, and native Indic scripts (Tamil, Sinhala).
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Optional

logger = logging.getLogger(__name__)

# Control characters to strip:
# ASCII 0x00-0x08, 0x0B-0x0C, 0x0E-0x1F, 0x7F-0x9F (excludes \t (0x09), \n (0x0A), \r (0x0D))
# Note: Zero-width joiner (\u200D) and Zero-width non-joiner (\u200C) are format characters
# in Unicode category 'Cf' and MUST BE PRESERVED for correct rendering of Tamil and Sinhala scripts.
_UNWANTED_CONTROL_CHARS_REGEX = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]"
)

# Various Unicode non-breaking and unusual space characters mapped to standard space
_NON_STANDARD_SPACES_REGEX = re.compile(
    r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]"
)

# Multiple horizontal whitespace characters (spaces/tabs) on the same line
_HORIZONTAL_WHITESPACE_REGEX = re.compile(r"[ \t]+")

# Excessive newlines (3 or more) to normalize down to 2 (paragraph break)
_EXCESSIVE_NEWLINES_REGEX = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    """Clean extracted document text while preserving language and structure.

    Processes raw extracted document text by:
    1. Validating input type.
    2. Normalizing Unicode representation using canonical NFC composition.
    3. Preserving Tamil, Sinhala, and international scripts, including ZWJ/ZWNJ.
    4. Removing null bytes and unwanted control characters.
    5. Normalizing varied Unicode whitespace to standard spaces.
    6. Collapsing excessive horizontal whitespace while preserving single-space separation.
    7. Standardizing line endings and collapsing excessive blank lines to preserve paragraphs.
    8. Preserving headings, punctuation, math formulas, and numbers intact.

    Args:
        text: Raw text string extracted from a document.

    Returns:
        Cleaned text string ready for narration preparation.

    Raises:
        TypeError: If text is not a string instance.
    """
    if text is None:
        raise TypeError("Input text must be a string, got None.")
    if not isinstance(text, str):
        raise TypeError(f"Input text must be a string, got {type(text).__name__}.")

    if not text.strip():
        logger.debug("clean_text received empty or whitespace-only input.")
        return ""

    logger.debug("Starting text cleaning (original length: %d chars).", len(text))

    # Step 1: Normalize line endings to standard Unix newline '\n'
    normalized_endings = text.replace("\r\n", "\n").replace("\r", "\n")

    # Step 2: Remove null bytes and unwanted ASCII control characters
    cleaned_controls = _UNWANTED_CONTROL_CHARS_REGEX.sub("", normalized_endings)

    # Step 3: Canonical Unicode normalization (NFC)
    # NFC composes precombined characters without decomposing essential glyphs in Indic scripts
    unicode_normalized = unicodedata.normalize("NFC", cleaned_controls)

    # Step 4: Normalize varied Unicode whitespace to ASCII space
    spaced_text = _NON_STANDARD_SPACES_REGEX.sub(" ", unicode_normalized)

    # Step 5: Process line by line to strip trailing/leading horizontal spaces on each line
    # while preserving headings and paragraph boundaries
    lines = spaced_text.split("\n")
    processed_lines = []
    for line in lines:
        # Collapse multiple horizontal spaces/tabs inside the line
        collapsed_line = _HORIZONTAL_WHITESPACE_REGEX.sub(" ", line).strip()
        processed_lines.append(collapsed_line)

    reconstructed_text = "\n".join(processed_lines)

    # Step 6: Collapse 3 or more consecutive newlines into 2 (paragraph break)
    final_text = _EXCESSIVE_NEWLINES_REGEX.sub("\n\n", reconstructed_text).strip()

    logger.debug("Completed text cleaning (cleaned length: %d chars).", len(final_text))
    return final_text
