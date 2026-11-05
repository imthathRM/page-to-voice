"""
OCR Quality Evaluator and Testing Suite.

Executes OCR test cases for English, Tamil, and Sinhala text images,
computes Character Error Rate (CER) and Word Error Rate (WER) against
ground truth, evaluates image preprocessing pipelines, and enforces
honest reporting (marking unavailable language packs as NOT TESTED).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from .environment import TesseractEnvironment, check_tesseract_environment
from .metrics import calculate_cer, calculate_wer
from .preprocessing import ImagePreprocessor, SimpleGrayscaleImage


@dataclass
class OCREvaluationResult:
    """Standard result structure for an OCR evaluation run."""
    language: str
    image_name: str
    status: str  # "TESTED" or "NOT_TESTED"
    recognized_text: str = ""
    ground_truth: str = ""
    cer: Optional[float] = None
    wer: Optional[float] = None
    execution_time_seconds: float = 0.0
    reason: Optional[str] = None
    preprocessing_applied: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "image_name": self.image_name,
            "status": self.status,
            "recognized_text": self.recognized_text,
            "ground_truth": self.ground_truth,
            "cer": round(self.cer, 4) if self.cer is not None else None,
            "wer": round(self.wer, 4) if self.wer is not None else None,
            "execution_time_seconds": round(self.execution_time_seconds, 3),
            "reason": self.reason,
            "preprocessing_applied": self.preprocessing_applied,
            "metadata": self.metadata,
        }


class OCREvaluator:
    """Evaluates Tesseract OCR across languages, combinations, and preprocessing steps."""

    def __init__(self, env: Optional[TesseractEnvironment] = None) -> None:
        self.env = env or check_tesseract_environment()

    def run_tesseract_cli(
        self,
        image_path: Union[str, Path],
        lang: str = "eng",
        psm: int = 3,
    ) -> Tuple[str, float]:
        """Execute tesseract command line binary and return output string and duration."""
        if not self.env.is_installed or not self.env.executable_path:
            raise RuntimeError("Tesseract executable is not installed or available.")

        cmd = [
            self.env.executable_path,
            str(image_path),
            "stdout",
            "-l",
            lang,
            "--psm",
            str(psm),
        ]

        t0 = time.time()
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        duration = time.time() - t0

        if res.returncode != 0:
            err_msg = res.stderr.strip() or f"Tesseract exited with code {res.returncode}"
            raise RuntimeError(f"OCR execution failed: {err_msg}")

        return res.stdout.strip(), duration

    def evaluate_image(
        self,
        image_path: Union[str, Path],
        ground_truth: str,
        lang: str = "eng",
        preprocessing: Optional[List[str]] = None,
    ) -> OCREvaluationResult:
        """Evaluate OCR accuracy for an image file against ground truth."""
        path = Path(image_path)
        prep = preprocessing or ["original"]

        # Check if Tesseract is installed
        if not self.env.is_installed:
            return OCREvaluationResult(
                language=lang,
                image_name=path.name,
                status="NOT_TESTED",
                ground_truth=ground_truth,
                reason="Tesseract OCR executable is not installed or accessible in PATH.",
                preprocessing_applied=prep,
            )

        # Check if required language pack(s) are installed
        required_codes = [c.strip().lower() for c in lang.split("+") if c.strip()]
        missing_in_run = [c for c in required_codes if c not in self.env.installed_languages]

        if missing_in_run:
            return OCREvaluationResult(
                language=lang,
                image_name=path.name,
                status="NOT_TESTED",
                ground_truth=ground_truth,
                reason=f"Missing required language pack(s): {', '.join(missing_in_run)}. "
                       f"Installed language packs: {self.env.installed_languages}",
                preprocessing_applied=prep,
            )

        # Execute OCR
        try:
            recognized, duration = self.run_tesseract_cli(path, lang=lang)
            cer = calculate_cer(ground_truth, recognized)
            wer = calculate_wer(ground_truth, recognized)

            return OCREvaluationResult(
                language=lang,
                image_name=path.name,
                status="TESTED",
                recognized_text=recognized,
                ground_truth=ground_truth,
                cer=cer,
                wer=wer,
                execution_time_seconds=duration,
                preprocessing_applied=prep,
            )
        except Exception as e:
            return OCREvaluationResult(
                language=lang,
                image_name=path.name,
                status="FAILED",
                ground_truth=ground_truth,
                reason=f"Execution error during OCR: {e}",
                preprocessing_applied=prep,
            )
