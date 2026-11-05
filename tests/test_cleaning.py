"""Unit tests for the Text Cleaning module."""

from __future__ import annotations

import unicodedata
import pytest

from page_to_voice.cleaning.text_cleaner import clean_text


def test_clean_text_english(sample_english_text: str) -> None:
    """Test cleaning standard English text with headings, tabs, and line breaks."""
    dirty_text = f"  \t {sample_english_text} \n\n\n\n  "
    cleaned = clean_text(dirty_text)

    assert "# Introduction to Artificial Intelligence" in cleaned
    assert "Dr. Alan Turing" in cleaned
    assert "accuracy rate!" in cleaned
    assert not cleaned.startswith(" ")
    assert not cleaned.endswith(" ")
    assert "\n\n\n" not in cleaned  # Max 2 consecutive line breaks


def test_clean_text_tamil(sample_tamil_text: str) -> None:
    """Test Tamil text cleaning and Unicode character preservation."""
    dirty_tamil = f"\x00\x05  {sample_tamil_text}  \t\t\n\n\n"
    cleaned = clean_text(dirty_tamil)

    assert "தமிழ் இலக்கியம்" in cleaned
    assert "திரு. பாரதியார்" in cleaned
    assert "டாக்டர். அப்துல் கலாம்" in cleaned
    assert "\x00" not in cleaned
    assert "\x05" not in cleaned


def test_clean_text_sinhala(sample_sinhala_text: str) -> None:
    """Test Sinhala text cleaning, Kunddaliya punctuation, and ZWJ preservation."""
    dirty_sinhala = f"  \x08{sample_sinhala_text}  \n\n\n\n"
    cleaned = clean_text(dirty_sinhala)

    assert "සිංහල සාහිත්‍යය" in cleaned
    assert "ආචාර්ය. කුමාරතුංග මුනිදාසයන්" in cleaned
    assert "ප්‍රබෝධයට" in cleaned  # Contains Rakaransaya with ZWJ
    assert "සැබවින්ම එය සත්‍යයකි෴" in cleaned
    assert "\x08" not in cleaned


def test_clean_text_preserves_zwj_and_zwnj() -> None:
    """Ensure Zero-Width Joiner (ZWJ) and Zero-Width Non-Joiner (ZWNJ) are not stripped."""
    # Sinhala word with ZWJ (Rakaransaya: ka + hal + ZWJ + ra)
    sinhala_word = "\u0D9A\u0DCA\u200D\u0DBB"  # ක්‍ර
    cleaned = clean_text(f"  {sinhala_word}  ")
    assert "\u200D" in cleaned
    assert cleaned == sinhala_word

    # Tamil word with ZWNJ
    tamil_with_zwnj = "க்\u200Cஷ"
    cleaned_tamil = clean_text(tamil_with_zwnj)
    assert "\u200C" in cleaned_tamil


def test_clean_text_unicode_normalization() -> None:
    """Ensure canonical Unicode normalization (NFC) is applied."""
    # Decomposed form: 'e' + combining acute accent (\u0301)
    decomposed = "Cafe\u0301"
    cleaned = clean_text(decomposed)
    # NFC composed form: 'é' (\u00E9)
    assert cleaned == "Café"
    assert unicodedata.is_normalized("NFC", cleaned)


def test_clean_text_mathematical_expressions(sample_math_text: str) -> None:
    """Verify that equations, superscripts, symbols, and math notation are preserved."""
    cleaned = clean_text(sample_math_text)
    assert "E = mc^2" in cleaned
    assert "a^2 + b^2 = c^2" in cleaned
    assert "x + y = 10" in cleaned
    assert "$1,250.75" in cleaned
    assert "15%" in cleaned


def test_clean_text_horizontal_spaces_and_tabs() -> None:
    """Ensure consecutive spaces and tabs are collapsed without corrupting single words."""
    raw = "Word1     \t\t   Word2       Word3\tWord4"
    cleaned = clean_text(raw)
    assert cleaned == "Word1 Word2 Word3 Word4"


def test_clean_text_excessive_newlines() -> None:
    """Ensure excessive blank lines (3+) are reduced to standard paragraph breaks (2)."""
    raw = "Paragraph One.\n\n\n\n\n\nParagraph Two.\n\n\n\nParagraph Three."
    cleaned = clean_text(raw)
    assert cleaned == "Paragraph One.\n\nParagraph Two.\n\nParagraph Three."


def test_clean_text_control_and_null_characters() -> None:
    """Ensure null bytes, bell, escape, and other unwanted controls are stripped."""
    raw = "Clean\x00Start\x01\x02\x07\x08\x0b\x0c\x0e\x1fEnd\x7f"
    cleaned = clean_text(raw)
    assert cleaned == "CleanStartEnd"


def test_clean_text_empty_and_whitespace_input() -> None:
    """Ensure empty or whitespace-only inputs return empty string safely."""
    assert clean_text("") == ""
    assert clean_text("   ") == ""
    assert clean_text("\n\n\t  \r\n") == ""


def test_clean_text_invalid_input_raises_type_error() -> None:
    """Ensure non-string input raises a TypeError."""
    with pytest.raises(TypeError, match="Input text must be a string"):
        clean_text(None)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Input text must be a string"):
        clean_text(12345)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Input text must be a string"):
        clean_text(["List of text"])  # type: ignore[arg-type]


def test_clean_text_large_document_efficiency() -> None:
    """Ensure text cleaning runs efficiently on large text documents (100,000+ characters)."""
    base_paragraph = (
        "This is a benchmark paragraph for performance testing.\n"
        "It includes numbers like 123.45 and symbols like $50.00.\n\n"
    )
    large_text = base_paragraph * 2000  # ~200,000 characters
    cleaned = clean_text(large_text)
    assert len(cleaned) > 100000
    assert "benchmark paragraph" in cleaned
