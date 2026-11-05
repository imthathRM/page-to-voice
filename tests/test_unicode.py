"""
Automated Tests for Multilingual Unicode Support.

Verifies:
- English text extraction fidelity.
- Tamil Unicode script extraction across all six formats.
- Sinhala Unicode script extraction across all six formats.
- Special characters, mathematical symbols, and typographical punctuation.
- Absence of character corruption, mojibake, or unexpected question-mark replacements.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

# Ensure backend is in path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from document_processing import parse_document

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
DOCS_DIR = FIXTURES_DIR / "documents"
EXPECTED_DIR = FIXTURES_DIR / "expected"


class TestMultilingualUnicode(unittest.TestCase):
    """Test suite for Unicode text fidelity (English, Tamil, Sinhala, Symbols)."""

    @classmethod
    def setUpClass(cls) -> None:
        expected_json_path = EXPECTED_DIR / "expected_text.json"
        with open(expected_json_path, "r", encoding="utf-8") as f:
            cls.expected_data = json.load(f)

        cls.sample_files = [
            "sample.txt",
            "sample.docx",
            "sample.pptx",
            "sample.epub",
            "sample.rtf",
            "sample.pdf",
        ]

    def test_english_text_extraction(self) -> None:
        """Verify English sentences and technical vocabulary are extracted accurately."""
        phrase = "Page to Voice is an intelligent audiobook generation"
        for filename in self.sample_files:
            with self.subTest(file=filename):
                path = DOCS_DIR / filename
                res = parse_document(path)
                self.assertIn(phrase, res.text)

    def test_tamil_unicode_extraction(self) -> None:
        """Verify Tamil script characters, ligatures, and vowel modifiers are extracted accurately."""
        # Key Tamil phrases from section 1 and section 2
        tamil_phrase_1 = "பக்கம் முதல் குரல் வரை"
        tamil_word_2 = "தமிழ்"

        for filename in self.sample_files:
            with self.subTest(file=filename):
                path = DOCS_DIR / filename
                res = parse_document(path)
                self.assertIn(tamil_phrase_1, res.text)
                self.assertIn(tamil_word_2, res.text)

    def test_sinhala_unicode_extraction(self) -> None:
        """Verify Sinhala script characters and diacritics are extracted accurately."""
        # Key Sinhala phrases from section 1 and section 2
        sinhala_phrase_1 = "පිටුවෙන් හඬට"
        sinhala_word_2 = "සිංහල"

        for filename in self.sample_files:
            with self.subTest(file=filename):
                path = DOCS_DIR / filename
                res = parse_document(path)
                self.assertIn(sinhala_phrase_1, res.text)
                self.assertIn(sinhala_word_2, res.text)

    def test_special_characters_and_symbols(self) -> None:
        """Verify typographical punctuation, currency symbols, and math notation."""
        symbols_to_check = [
            "©",  # Copyright
            "®",  # Registered trademark
            "™",  # Trademark
            "€",  # Euro currency
            "£",  # Pound currency
            "¥",  # Yen currency
            "α",  # Greek alpha
            "β",  # Greek beta
            "γ",  # Greek gamma
            "—",  # Em-dash
            "…",  # Ellipsis
        ]

        for filename in self.sample_files:
            with self.subTest(file=filename):
                path = DOCS_DIR / filename
                res = parse_document(path)
                for sym in symbols_to_check:
                    self.assertIn(
                        sym,
                        res.text,
                        f"Symbol '{sym}' missing in extraction of {filename}",
                    )

    def test_no_unicode_corruption_or_replacement_markers(self) -> None:
        """Verify extracted text does not contain Unicode replacement character U+FFFD."""
        for filename in self.sample_files:
            with self.subTest(file=filename):
                path = DOCS_DIR / filename
                res = parse_document(path)
                self.assertNotIn("\ufffd", res.text)
                # Verify that Tamil and Sinhala were not converted to question marks "???"
                self.assertNotIn("????", res.text)


if __name__ == "__main__":
    unittest.main()
