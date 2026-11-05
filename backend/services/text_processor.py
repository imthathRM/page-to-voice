import re
import unicodedata
from typing import Tuple, Dict


def clean_text(text: str) -> str:
    """
    Clean extracted raw text:
    - Normalizes Unicode using NFC to preserve composite glyphs in Tamil and Sinhala.
    - Replaces odd control characters and non-breaking spaces while keeping basic whitespace.
    - Strips trailing spaces per line.
    - Collapses multiple horizontal spaces into a single space.
    - Collapses 3 or more consecutive blank lines into exactly 2 blank lines (paragraph breaks).
    - Preserves meaningful punctuation: periods, commas, exclamation marks, question marks, quotes.
    - Strictly protects Tamil (\u0B80-\u0BFF) and Sinhala (\u0D80-\u0DFF) scripts.
    """
    if not text:
        return ""

    # Normalize Unicode (NFC keeps combined characters intact)
    normalized = unicodedata.normalize("NFC", text)

    # Replace non-breaking spaces and line/paragraph separators with regular spaces/newlines
    normalized = normalized.replace("\u00A0", " ").replace("\u200B", "").replace("\uFEFF", "")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

    # Remove non-printable control characters except newline and tab
    normalized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", normalized)

    lines = normalized.split("\n")
    cleaned_lines = []
    for line in lines:
        # Collapse multiple spaces or tabs into a single space
        line = re.sub(r"[ \t]+", " ", line).strip()
        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines)

    # Collapse 3 or more newlines into double newlines (paragraphs)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def detect_language(text: str) -> Tuple[str, Dict[str, float]]:
    """
    Detect language based on Unicode script frequency:
    - English ('en')
    - Tamil ('ta')
    - Sinhala ('si')
    Returns: (detected_code, confidence_scores_dict)
    """
    if not text or not text.strip():
        return "en", {"en": 1.0, "ta": 0.0, "si": 0.0}

    # Count script character occurrences
    sinhala_chars = len(re.findall(r"[\u0D80-\u0DFF]", text))
    tamil_chars = len(re.findall(r"[\u0B80-\u0BFF]", text))
    latin_chars = len(re.findall(r"[a-zA-Z]", text))

    total = sinhala_chars + tamil_chars + latin_chars
    if total == 0:
        return "en", {"en": 1.0, "ta": 0.0, "si": 0.0}

    scores = {
        "si": round(sinhala_chars / total, 3),
        "ta": round(tamil_chars / total, 3),
        "en": round(latin_chars / total, 3),
    }

    # Pick the highest score
    detected = max(scores, key=scores.get)
    return detected, scores

