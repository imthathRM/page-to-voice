"""
Automated Tests for OCR Evaluation, Language Packs, and Preprocessing.

Verifies:
- Character Error Rate (CER) calculation.
- Word Error Rate (WER) calculation.
- Tesseract environment and language pack diagnostics.
- Graceful handling of missing language packs (marking as NOT TESTED).
- Multi-language combination checks (eng+tam, eng+sin, tam+sin).
- Image preprocessing routines (grayscale, resize, noise removal, binarize, deskew).
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

from document_processing.ocr import (
    ImagePreprocessor,
    OCREvaluator,
    SimpleGrayscaleImage,
    calculate_cer,
    calculate_wer,
    check_tesseract_environment,
    levenshtein_distance,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
OCR_DIR = FIXTURES_DIR / "ocr"


class TestOCREvaluationAndPreprocessing(unittest.TestCase):
    """Test suite for OCR metrics, environment checks, and preprocessing."""

    def test_levenshtein_distance(self) -> None:
        """Verify dynamic programming Levenshtein distance calculations."""
        self.assertEqual(levenshtein_distance("kitten", "sitting"), 3)
        self.assertEqual(levenshtein_distance("hello", "hello"), 0)
        self.assertEqual(levenshtein_distance("", "test"), 4)
        self.assertEqual(levenshtein_distance("apple", ""), 5)

    def test_cer_calculation_english(self) -> None:
        """Verify CER on English test cases."""
        ref = "Page to Voice"
        hyp = "Page to Voice"
        self.assertEqual(calculate_cer(ref, hyp), 0.0)

        # 1 character substitution: "P" -> "R" (1 / 13)
        hyp_sub = "Rage to Voice"
        self.assertAlmostEqual(calculate_cer(ref, hyp_sub), 1.0 / 13.0, places=4)

        # 1 character deletion: "to " missing
        hyp_del = "Page Voice"
        self.assertGreater(calculate_cer(ref, hyp_del), 0.0)

    def test_cer_calculation_indic_unicode(self) -> None:
        """Verify CER on Tamil and Sinhala Unicode sequences."""
        tam_ref = "பக்கம் முதல் குரல் வரை"
        tam_hyp = "பக்கம் முதல் குரல் வரை"
        self.assertEqual(calculate_cer(tam_ref, tam_hyp), 0.0)

        sin_ref = "පිටුවෙන් හඬට"
        sin_hyp = "පිටුවෙන් හඬට"
        self.assertEqual(calculate_cer(sin_ref, sin_hyp), 0.0)

    def test_wer_calculation(self) -> None:
        """Verify Word Error Rate (WER) calculations."""
        ref = "The quick brown fox jumps over the lazy dog"
        hyp = "The quick brown fox jumps over the lazy dog"
        self.assertEqual(calculate_wer(ref, hyp), 0.0)

        # 1 word substituted out of 9 words: 1 / 9
        hyp_sub = "The fast brown fox jumps over the lazy dog"
        self.assertAlmostEqual(calculate_wer(ref, hyp_sub), 1.0 / 9.0, places=4)

    def test_tesseract_environment_inspection(self) -> None:
        """Verify Tesseract environment inspection returns diagnostic fields."""
        env = check_tesseract_environment()
        d = env.to_dict()

        self.assertIn("is_installed", d)
        self.assertIn("executable_path", d)
        self.assertIn("installed_languages", d)
        self.assertIn("missing_languages", d)
        self.assertIn("combined_support", d)
        self.assertIn("python_bindings", d)

        # Ensure installation instructions are provided
        instructions = env.get_windows_installation_instructions()
        self.assertIn("Windows Installation Guide", instructions)
        self.assertIn("Tamil", instructions)
        self.assertIn("Sinhala", instructions)

    def test_missing_language_packs_handled_gracefully(self) -> None:
        """Verify OCREvaluator marks unavailable languages as NOT_TESTED without crashing."""
        evaluator = OCREvaluator()
        gt_path = OCR_DIR / "ground_truth.json"

        if gt_path.exists():
            with open(gt_path, "r", encoding="utf-8") as f:
                gt_data = json.load(f)

            # Test evaluation on each image fixture
            for img_name, data in gt_data.items():
                img_path = OCR_DIR / img_name
                if not img_path.exists():
                    continue

                res = evaluator.evaluate_image(
                    image_path=img_path,
                    ground_truth=data["text"],
                    lang=data["language"],
                )

                # Status must be either TESTED or NOT_TESTED (never uncaught crash)
                self.assertIn(res.status, ["TESTED", "NOT_TESTED", "FAILED"])
                if res.status == "NOT_TESTED":
                    self.assertIsNotNone(res.reason)
                    self.assertIsNone(res.cer)
                    self.assertIsNone(res.wer)
                elif res.status == "TESTED":
                    self.assertIsNotNone(res.cer)
                    self.assertIsNotNone(res.wer)

    def test_preprocessing_grayscale(self) -> None:
        """Verify grayscale conversion."""
        img = SimpleGrayscaleImage(50, 50)
        gray = ImagePreprocessor.to_grayscale(img)
        self.assertEqual(gray.width, 50)
        self.assertEqual(gray.height, 50)

    def test_preprocessing_resize(self) -> None:
        """Verify image resizing scales dimensions accurately."""
        img = SimpleGrayscaleImage(100, 50)
        resized = ImagePreprocessor.resize(img, scale_factor=2.0)
        self.assertEqual(resized.width, 200)
        self.assertEqual(resized.height, 100)

    def test_preprocessing_noise_removal(self) -> None:
        """Verify median filter suppresses solitary noise pixels."""
        img = SimpleGrayscaleImage(10, 10)
        # Background is white (255); add single black noise pixel at (5, 5)
        img.set_pixel(5, 5, 0)
        denoised = ImagePreprocessor.remove_noise(img, window_size=3)
        # The noise pixel should be replaced by median neighbor (white: 255)
        self.assertEqual(denoised.get_pixel(5, 5), 255)

    def test_preprocessing_binarization_otsu(self) -> None:
        """Verify Otsu binarization outputs strictly pure black and white (0 or 255)."""
        img = SimpleGrayscaleImage(20, 20)
        # Add some gray text pixels
        for y in range(5, 15):
            for x in range(5, 15):
                img.set_pixel(x, y, 40)  # dark text

        binary = ImagePreprocessor.binarize(img)
        for y in range(binary.height):
            for x in range(binary.width):
                val = binary.get_pixel(x, y)
                self.assertIn(val, (0, 255))

    def test_preprocessing_deskew(self) -> None:
        """Verify deskew detection function operates on image."""
        img = SimpleGrayscaleImage(40, 40)
        deskewed, angle = ImagePreprocessor.deskew(img)
        self.assertEqual(deskewed.width, 40)
        self.assertEqual(deskewed.height, 40)
        self.assertIsInstance(angle, float)

    def test_preprocessing_pipeline_execution(self) -> None:
        """Verify applying multiple preprocessing steps in pipeline."""
        img = SimpleGrayscaleImage(40, 40)
        pipeline = ["grayscale", "resize", "noise_removal", "binarize"]
        processed, info = ImagePreprocessor.apply_pipeline(img, pipeline)

        self.assertEqual(processed.width, 80)
        self.assertEqual(processed.height, 80)
        self.assertTrue(len(info["applied"]) >= 4)


if __name__ == "__main__":
    unittest.main()
