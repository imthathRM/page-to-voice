"""Unit tests for the Narration Preparation module."""

from __future__ import annotations

import pytest

from page_to_voice.narration.boundary_detector import split_sentences
from page_to_voice.narration.chunker import prepare_narration
from page_to_voice.narration.models import Chapter


def test_split_sentences_english_abbreviations_and_decimals() -> None:
    """Verify that abbreviations like 'Dr.', 'Mr.', 'p.m.' and decimals like '3.14' do not split sentences prematurely."""
    text = (
        "Dr. Smith met Mr. Brown at 3.14 p.m. in Washington, D.C. "
        "They discussed the new study! Did it succeed? Yes, it did."
    )
    sentences = split_sentences(text)
    assert len(sentences) == 4
    assert sentences[0] == "Dr. Smith met Mr. Brown at 3.14 p.m. in Washington, D.C."
    assert sentences[1] == "They discussed the new study!"
    assert sentences[2] == "Did it succeed?"
    assert sentences[3] == "Yes, it did."


def test_split_sentences_tamil() -> None:
    """Verify sentence boundary detection for Tamil with honorifics."""
    text = (
        "திரு. பாரதியார் ஒரு கவிஞர் ஆவார். அவரது கவிதைகள் சுதந்திர உணர்வை ஊட்டின! "
        "நீங்கள் அதை படித்திருக்கிறீர்களா? ஆம், படித்தேன்."
    )
    sentences = split_sentences(text)
    assert len(sentences) == 4
    assert sentences[0] == "திரு. பாரதியார் ஒரு கவிஞர் ஆவார்."
    assert sentences[1] == "அவரது கவிதைகள் சுதந்திர உணர்வை ஊட்டின!"
    assert sentences[2] == "நீங்கள் அதை படித்திருக்கிறீர்களா?"
    assert sentences[3] == "ஆம், படித்தேன்."


def test_split_sentences_sinhala_kunddaliya() -> None:
    """Verify sentence boundary detection for Sinhala, including honorifics and Kunddaliya."""
    text = (
        "ආචාර්ය. කුමාරතුංග මුනිදාසයන් විශිෂ්ට විය. "
        "පොතක් කියවීමෙන් මිනිසා සම්පූර්ණ වේ! ඔබ එකඟද? "
        "සැබවින්ම එය සත්‍යයකි෴"
    )
    sentences = split_sentences(text)
    assert len(sentences) == 4
    assert sentences[0] == "ආචාර්ය. කුමාරතුංග මුනිදාසයන් විශිෂ්ට විය."
    assert sentences[1] == "පොතක් කියවීමෙන් මිනිසා සම්පූර්ණ වේ!"
    assert sentences[2] == "ඔබ එකඟද?"
    assert "සැබවින්ම එය සත්‍යයකි෴" in sentences[3]


def test_prepare_narration_chunk_size_limits() -> None:
    """Verify that chunks respect max_chars limit and group multiple sentences."""
    text = (
        "Sentence number one is short. "
        "Sentence number two is also short. "
        "Sentence number three is somewhat longer. "
        "Sentence number four concludes this paragraph."
    )
    plan = prepare_narration(text=text, max_chars=80)
    assert plan.total_chunks > 1
    for chunk in plan.chunks:
        assert len(chunk.text) <= 80
        assert chunk.character_count == len(chunk.text)
        assert chunk.word_count > 0
        assert chunk.estimated_duration_seconds > 0.0


def test_prepare_narration_preserves_chunk_ordering() -> None:
    """Verify that chunk indices are strictly sequential and monotonically increasing."""
    text = (
        "First sentence. Second sentence. Third sentence. "
        "Fourth sentence. Fifth sentence. Sixth sentence."
    )
    plan = prepare_narration(text=text, max_chars=40)
    indices = [c.index for c in plan.chunks]
    assert indices == list(range(len(plan.chunks)))
    assert len(indices) >= 2


def test_prepare_narration_chapters_metadata(sample_chapters: list[Chapter]) -> None:
    """Verify chapter-wise narration structuring and preservation of chapter metadata."""
    plan = prepare_narration(chapters=sample_chapters, max_chars=100)

    assert plan.total_chunks >= 2
    # Check that chapter titles are mapped correctly onto chunks
    ch1_chunks = [c for c in plan.chunks if c.chapter_title == "Chapter 1: The Beginning"]
    ch2_chunks = [c for c in plan.chunks if c.chapter_title == "Chapter 2: The Adventure"]

    assert len(ch1_chunks) > 0
    assert len(ch2_chunks) > 0
    assert ch1_chunks[0].section_title == "Part A"
    assert ch2_chunks[0].section_title == "Part B"


def test_prepare_narration_unusually_long_sentence() -> None:
    """Verify that an unusually long sentence exceeding max_chars is split safely without cutting words."""
    long_sentence = (
        "This is an extraordinarily long sentence designed to test the chunking algorithm, "
        "which should gracefully split on comma clauses; furthermore, it should ensure that "
        "no individual English, Tamil, or Sinhala words are severed in the middle of a token."
    )
    plan = prepare_narration(text=long_sentence, max_chars=80)
    assert plan.total_chunks >= 2
    reconstructed = " ".join(c.text for c in plan.chunks)
    # Ensure words were not cut
    for word in long_sentence.split():
        clean_word = word.strip(",;")
        assert clean_word in reconstructed


def test_prepare_narration_empty_input() -> None:
    """Verify that empty text or empty chapters list returns an empty NarrationPlan safely."""
    plan_text = prepare_narration(text="")
    assert plan_text.total_chunks == 0
    assert plan_text.chunks == []
    assert plan_text.total_characters == 0

    plan_none = prepare_narration(text=None, chapters=[])
    assert plan_none.total_chunks == 0
    assert plan_none.chunks == []


def test_prepare_narration_invalid_max_chars_raises_value_error() -> None:
    """Verify that non-positive max_chars raises ValueError."""
    with pytest.raises(ValueError, match="max_chars must be a positive integer"):
        prepare_narration(text="Valid text", max_chars=0)

    with pytest.raises(ValueError, match="max_chars must be a positive integer"):
        prepare_narration(text="Valid text", max_chars=-10)
