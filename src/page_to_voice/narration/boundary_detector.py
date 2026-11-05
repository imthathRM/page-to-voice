"""Sentence boundary detection module for Page to Voice.

Provides accurate, multi-language sentence boundary detection supporting English,
Tamil, and Sinhala text. Distinguishes true sentence terminators from abbreviations,
decimal numbers, initials, and embedded punctuation.
"""

from __future__ import annotations

import logging
import re
from typing import List

logger = logging.getLogger(__name__)

# Common English abbreviations (case-insensitive) that end with a dot but do not end sentences
_ENGLISH_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "vs", "etc", "eg", "ie",
    "approx", "apt", "dept", "est", "fig", "gen", "gov", "inc", "corp",
    "ltd", "vol", "no", "rev", "st", "al", "co", "jan", "feb", "mar",
    "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
}

# Common Tamil honorifics / abbreviations
_TAMIL_ABBREVIATIONS = {
    "திரு", "திருமதி", "செல்வி", "டாக்டர்", "பேரா", "வ", "இல",
}

# Common Sinhala honorifics / abbreviations
_SINHALA_ABBREVIATIONS = {
    "මයා", "මිය", "මෙනවිය", "ආචාර්ය", "මහා", "ගරු", "පූජ්‍ය", "පෙ", "ව", "අං",
}

# Regex to match candidate sentence terminators:
# 1. Punctuation: ., !, ?, Sinhala Kunddaliya (\u0DF4), Danda (\u0964), Double Danda (\u0965)
# 2. Followed by optional closing quotes/parentheses: '"”’' ) ] }
# 3. Followed by either whitespace, newline, or end of string
_CANDIDATE_TERMINATOR_REGEX = re.compile(
    r"([.!?\u0964\u0965\u0DF4]+['\"”’\)\]}]*)(?:\s+|\Z)"
)

# Regex to detect if dot is a decimal point between numbers (e.g., 3.14, 10.5)
_DECIMAL_NUMBER_REGEX = re.compile(r"^\d+\.\d+$")

# Regex to match single-letter initials (e.g., "A." or "J.")
_INITIAL_REGEX = re.compile(r"^[A-Za-z]\.$")


def _is_abbreviation(token: str) -> bool:
    """Check if a token ending with a period is a known abbreviation."""
    cleaned = token.rstrip(".!?\"'”’)]}").strip()
    lower = cleaned.lower()

    if lower in _ENGLISH_ABBREVIATIONS:
        return True
    if cleaned in _TAMIL_ABBREVIATIONS:
        return True
    if cleaned in _SINHALA_ABBREVIATIONS:
        return True

    # Single uppercase initial e.g., "J." or "A."
    if _INITIAL_REGEX.match(token.rstrip("\"'”’)]}")):
        return True

    return False


def split_sentences(text: str) -> List[str]:
    """Split cleaned text into distinct sentences across English, Tamil, and Sinhala.

    Preserves paragraph breaks, headings, and handles abbreviations without splitting.

    Args:
        text: Input string (ideally already cleaned via clean_text).

    Returns:
        List of non-empty sentence strings in original order.
    """
    if not text or not text.strip():
        return []

    # First split on explicit paragraph boundaries (double newlines)
    paragraphs = text.split("\n\n")
    all_sentences: List[str] = []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # If the paragraph is a single line without standard ending punctuation (e.g. heading),
        # preserve it as its own unit if short or standalone
        sentences_in_para = _split_paragraph(paragraph)
        all_sentences.extend(sentences_in_para)

    return all_sentences


def _split_paragraph(paragraph: str) -> List[str]:
    """Split a single paragraph into individual sentences."""
    if not paragraph:
        return []

    # If the paragraph contains explicit single linebreaks (e.g., headings or poetry),
    # process line-by-line when appropriate
    lines = [line.strip() for line in paragraph.split("\n") if line.strip()]
    if len(lines) > 1 and all(not line.endswith((".", "!", "?", "\u0964", "\u0965", "\u0DF4")) for line in lines[:-1]):
        # Lines without terminal punctuation (e.g. Title \n Subtitle) - treat each line as a distinct unit
        result: List[str] = []
        for line in lines:
            result.extend(_split_prose_block(line))
        return result

    return _split_prose_block(paragraph)


def _split_prose_block(prose: str) -> List[str]:
    """Split a block of prose text into sentences using linguistic heuristics."""
    sentences: List[str] = []
    start_idx = 0
    length = len(prose)

    for match in _CANDIDATE_TERMINATOR_REGEX.finditer(prose):
        punct = match.group(1)
        end_idx = match.end()
        match_start = match.start(1)

        # Extract the word token preceding this punctuation
        prev_text = prose[start_idx:match_start].strip()
        words = prev_text.split()
        last_word = words[-1] if words else ""

        # Check conditions where dot is NOT a sentence boundary:
        # 1. Decimal number (e.g. 3.14)
        if "." in punct and match_start > 0 and end_idx < length:
            prev_char = prose[match_start - 1] if match_start > 0 else ""
            next_char = prose[end_idx] if end_idx < length else ""
            if prev_char.isdigit() and (next_char.isdigit() or (punct == "." and prose[match_start:match_start+2] == ". " and next_char.islower())):
                continue

        # 2. If a period is followed by a lowercase letter, the sentence continues
        if "." in punct and end_idx < length:
            remaining = prose[end_idx:].lstrip()
            if remaining and remaining[0].islower():
                continue

        # 3. Known abbreviation (e.g., Dr., Mr., etc.)
        full_token = last_word + punct
        if "." in punct and _is_abbreviation(full_token):
            # For titles like "Dr. Smith", the next word is uppercase but it's still an abbreviation
            if full_token.rstrip(".!?\"'”’)]}").lower() in ("mr", "mrs", "ms", "dr", "prof", "sr", "jr", "திரு", "ආචාර්ය", "මහා"):
                continue

        # Valid sentence boundary found
        sentence = prose[start_idx:end_idx].strip()
        if sentence:
            sentences.append(sentence)
        start_idx = end_idx

    # Capture any trailing text after the last punctuation
    if start_idx < length:
        trailing = prose[start_idx:].strip()
        if trailing:
            sentences.append(trailing)

    return sentences
