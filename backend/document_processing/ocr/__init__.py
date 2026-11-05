"""
OCR Module for Page to Voice Document Processing.

Provides Tesseract environment diagnostics, language pack verification,
Character Error Rate (CER) and Word Error Rate (WER) metrics,
image preprocessing pipelines, and structured OCR evaluation.
"""

from .environment import TesseractEnvironment, check_tesseract_environment
from .evaluator import OCREvaluationResult, OCREvaluator
from .metrics import calculate_cer, calculate_wer, levenshtein_distance
from .preprocessing import ImagePreprocessor, SimpleGrayscaleImage

__all__ = [
    "TesseractEnvironment",
    "check_tesseract_environment",
    "calculate_cer",
    "calculate_wer",
    "levenshtein_distance",
    "ImagePreprocessor",
    "SimpleGrayscaleImage",
    "OCREvaluator",
    "OCREvaluationResult",
]
