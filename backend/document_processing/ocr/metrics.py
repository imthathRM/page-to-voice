"""
OCR Evaluation Metrics: Character Error Rate (CER) and Word Error Rate (WER).

Computes standardized Levenshtein-based error rates for evaluating OCR quality
against ground-truth reference texts.
"""

from __future__ import annotations

import unicodedata
from typing import List, Sequence, TypeVar

T = TypeVar("T")


def levenshtein_distance(seq1: Sequence[T], seq2: Sequence[T]) -> int:
    """Compute the minimum edit distance (insertions, deletions, substitutions)
    between two sequences using dynamic programming with O(min(N, M)) memory.
    """
    if seq1 == seq2:
        return 0
    if not seq1:
        return len(seq2)
    if not seq2:
        return len(seq1)

    # Ensure seq1 is the shorter sequence for O(len(seq1)) space
    if len(seq1) > len(seq2):
        seq1, seq2 = seq2, seq1

    previous_row = list(range(len(seq1) + 1))
    current_row = [0] * (len(seq1) + 1)

    for i, elem2 in enumerate(seq2):
        current_row[0] = i + 1
        for j, elem1 in enumerate(seq1):
            insertion = current_row[j] + 1
            deletion = previous_row[j + 1] + 1
            substitution = previous_row[j] + (0 if elem1 == elem2 else 1)
            current_row[j + 1] = min(insertion, deletion, substitution)
        previous_row, current_row = current_row, previous_row

    return previous_row[len(seq1)]


def normalize_text_for_evaluation(text: str) -> str:
    """Normalize Unicode text into NFC canonical composition and standardize whitespace."""
    if not text:
        return ""
    # NFC normalization ensures composed characters (e.g. Tamil / Sinhala diacritics) match
    normalized = unicodedata.normalize("NFC", text)
    # Collapse multiple spaces and line breaks to single space
    normalized = " ".join(normalized.split())
    return normalized.strip()


def calculate_cer(reference: str, hypothesis: str, normalize: bool = True) -> float:
    """Calculate Character Error Rate (CER).

    Formula: CER = Levenshtein_Distance(reference, hypothesis) / len(reference)

    Args:
        reference: Ground-truth reference text.
        hypothesis: OCR-generated hypothesis text.
        normalize: Whether to normalize Unicode NFC and collapse whitespace.

    Returns:
        float: CER value (0.0 means perfect match; > 0.0 indicates errors; can exceed 1.0).
    """
    ref = normalize_text_for_evaluation(reference) if normalize else reference
    hyp = normalize_text_for_evaluation(hypothesis) if normalize else hypothesis

    if not ref:
        return 0.0 if not hyp else 1.0

    edit_dist = levenshtein_distance(list(ref), list(hyp))
    return edit_dist / len(ref)


def calculate_wer(reference: str, hypothesis: str, normalize: bool = True) -> float:
    """Calculate Word Error Rate (WER).

    Formula: WER = Levenshtein_Distance(ref_words, hyp_words) / len(ref_words)

    Args:
        reference: Ground-truth reference text.
        hypothesis: OCR-generated hypothesis text.
        normalize: Whether to normalize Unicode NFC and collapse whitespace.

    Returns:
        float: WER value (0.0 means perfect match; > 0.0 indicates errors; can exceed 1.0).
    """
    ref = normalize_text_for_evaluation(reference) if normalize else reference
    hyp = normalize_text_for_evaluation(hypothesis) if normalize else hypothesis

    ref_words = ref.split()
    hyp_words = hyp.split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    edit_dist = levenshtein_distance(ref_words, hyp_words)
    return edit_dist / len(ref_words)
