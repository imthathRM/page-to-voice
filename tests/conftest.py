"""Pytest fixtures and test data samples for Page to Voice test suites."""

from __future__ import annotations

import math
import struct
from pathlib import Path
from typing import Generator
import pytest

from page_to_voice.narration.models import Chapter


@pytest.fixture
def sample_english_text() -> str:
    """Sample English text containing paragraphs, headings, abbreviations, and dialogue."""
    return (
        "# Introduction to Artificial Intelligence\n\n"
        "Artificial Intelligence (AI) represents a landmark leap in modern technology.\n"
        "Dr. Alan Turing asked: \"Can machines think?\" This was in the mid-20th century.\n\n"
        "Prof. Smith and Mr. Brown published a paper in Washington, D.C. at 3.14 p.m. "
        "The model achieved a 98.5% accuracy rate! Did everyone agree with the results? "
        "Of course not."
    )


@pytest.fixture
def sample_tamil_text() -> str:
    """Sample Tamil text with native Unicode scripts, honorifics, and punctuation."""
    return (
        "# தமிழ் இலக்கியம்\n\n"
        "திரு. பாரதியார் ஒரு சிறந்த கவிஞர் ஆவார். அவரது கவிதைகள் சுதந்திர உணர்வை ஊட்டின!\n"
        "டாக்டர். அப்துல் கலாம் அவர்கள் இளைஞர்களுக்கு ஊக்கமளித்தார். நீங்கள் கனவு காண வேண்டும்? "
        "ஆம், நிச்சயமாக!"
    )


@pytest.fixture
def sample_sinhala_text() -> str:
    """Sample Sinhala text with native Unicode characters (including ZWJ), honorifics, and punctuation."""
    return (
        "# සිංහල සාහිත්‍යය\n\n"
        "ආචාර්ය. කුමාරතුංග මුනිදාසයන් සිංහල භාෂාවේ ප්‍රබෝධයට මහඟු මෙහෙවරක් කළේය.\n"
        "පොතක් කියවීමෙන් මිනිසා සම්පූර්ණ වේ! ඔබ එය විශ්වාස කරනවාද? "
        "සැබවින්ම එය සත්‍යයකි෴"
    )


@pytest.fixture
def sample_math_text() -> str:
    """Sample text with mathematical expressions, numbers, and symbols."""
    return (
        "In physics, Einstein established that E = mc^2.\n"
        "The Pythagorean theorem states: a^2 + b^2 = c^2.\n"
        "Given x + y = 10 and 2x - y = 5, we can solve for x & y. "
        "The integral of f(x)dx = F(x) + C. The cost was $1,250.75 (a 15% discount)."
    )


@pytest.fixture
def sample_chapters() -> list[Chapter]:
    """Sample structured chapters for testing chapter-based narration."""
    return [
        Chapter(
            title="Chapter 1: The Beginning",
            content="Once upon a time in a ancient land. A journey began. The heroes set forth.",
            section_title="Part A",
        ),
        Chapter(
            title="Chapter 2: The Adventure",
            content="They traveled across vast mountains and deep valleys! What challenges awaited them?",
            section_title="Part B",
        ),
    ]


@pytest.fixture
def synthetic_pcm_audio() -> bytes:
    """Generate 0.2 seconds of synthetic 440 Hz sine wave PCM audio (16-bit, 24000 Hz, mono)."""
    sample_rate = 24000
    duration = 0.2
    frequency = 440.0
    total_samples = int(sample_rate * duration)
    amplitude = 16000

    pcm_bytes = bytearray()
    for i in range(total_samples):
        sample = int(amplitude * math.sin(2.0 * math.pi * frequency * i / sample_rate))
        pcm_bytes.extend(struct.pack("<h", sample))

    return bytes(pcm_bytes)


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary directory for audio outputs during tests."""
    out_dir = tmp_path / "test_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    yield out_dir
