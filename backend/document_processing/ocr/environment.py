"""
Tesseract OCR Environment Inspection and Diagnostic Module.

Detects Tesseract OCR executable, version, installed language packs
(specifically `eng`, `tam`, `sin`), and Python integration libraries.
Provides structured diagnostic reporting and operating system-specific
installation instructions when dependencies or language packs are missing.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List, Optional


class TesseractEnvironment:
    """Diagnostic state and capability detector for Tesseract OCR."""

    COMMON_WINDOWS_PATHS = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        r"C:\tools\tesseract\tesseract.exe",
    ]

    REQUIRED_LANGUAGES = ["eng", "tam", "sin"]

    def __init__(self) -> None:
        self.executable_path: Optional[str] = None
        self.version: Optional[str] = None
        self.installed_languages: List[str] = []
        self.is_installed: bool = False

        self.has_pytesseract: bool = False
        self.has_pillow: bool = False
        self.has_opencv: bool = False

        self._inspect()

    def _inspect(self) -> None:
        """Inspect system environment for Tesseract binary and Python modules."""
        # Check Python bindings
        try:
            import pytesseract
            self.has_pytesseract = True
        except ImportError:
            self.has_pytesseract = False

        try:
            import PIL
            self.has_pillow = True
        except ImportError:
            self.has_pillow = False

        try:
            import cv2
            self.has_opencv = True
        except ImportError:
            self.has_opencv = False

        # Locate tesseract executable
        # 1. Check PATH
        path_in_env = shutil.which("tesseract")
        if path_in_env:
            self.executable_path = path_in_env
        else:
            # 2. Check standard Windows installation directories
            for candidate in self.COMMON_WINDOWS_PATHS:
                if Path(candidate).exists() and Path(candidate).is_file():
                    self.executable_path = candidate
                    break

        if not self.executable_path:
            self.is_installed = False
            return

        # Tesseract binary found: query version and language packs
        self.is_installed = True
        try:
            res_ver = subprocess.run(
                [self.executable_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # First line usually contains version, e.g. "tesseract 5.3.3"
            if res_ver.stdout:
                self.version = res_ver.stdout.splitlines()[0].strip()
            elif res_ver.stderr:
                self.version = res_ver.stderr.splitlines()[0].strip()
        except Exception:
            self.version = "Unknown (execution error)"

        # Query installed languages
        try:
            res_langs = subprocess.run(
                [self.executable_path, "--list-langs"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = res_langs.stdout or res_langs.stderr
            lines = [l.strip() for l in output.splitlines() if l.strip()]
            # First line is often header "List of available languages (X):"
            langs = []
            for l in lines:
                if "list of available languages" in l.lower() or ":" in l:
                    continue
                langs.append(l.lower())
            self.installed_languages = sorted(list(set(langs)))
        except Exception:
            self.installed_languages = []

    @property
    def has_english(self) -> bool:
        return "eng" in self.installed_languages

    @property
    def has_tamil(self) -> bool:
        return "tam" in self.installed_languages

    @property
    def has_sinhala(self) -> bool:
        return "sin" in self.installed_languages

    @property
    def missing_languages(self) -> List[str]:
        return [l for l in self.REQUIRED_LANGUAGES if l not in self.installed_languages]

    def supports_combination(self, lang_combo: str) -> bool:
        """Check if a multi-language combination (e.g. 'eng+tam') is fully supported."""
        if not self.is_installed:
            return False
        codes = [c.strip().lower() for c in lang_combo.split("+") if c.strip()]
        return all(code in self.installed_languages for code in codes)

    def to_dict(self) -> Dict[str, Any]:
        """Return diagnostic dictionary."""
        return {
            "is_installed": self.is_installed,
            "executable_path": self.executable_path,
            "version": self.version,
            "installed_languages": self.installed_languages,
            "missing_languages": self.missing_languages,
            "has_english": self.has_english,
            "has_tamil": self.has_tamil,
            "has_sinhala": self.has_sinhala,
            "combined_support": {
                "eng+tam": self.supports_combination("eng+tam"),
                "eng+sin": self.supports_combination("eng+sin"),
                "tam+sin": self.supports_combination("tam+sin"),
            },
            "python_bindings": {
                "pytesseract": self.has_pytesseract,
                "pillow": self.has_pillow,
                "opencv": self.has_opencv,
            },
        }

    @staticmethod
    def get_windows_installation_instructions() -> str:
        """Return step-by-step instructions for installing Tesseract and missing language packs on Windows."""
        return (
            "### Windows Installation Guide for Tesseract OCR & Language Packs\n\n"
            "1. **Download Tesseract Installer for Windows:**\n"
            "   - Download the official UB-Mannheim 64-bit installer from GitHub:\n"
            "     https://github.com/UB-Mannheim/tesseract/wiki\n"
            "   - File: `tesseract-ocr-w64-setup-5.3.3.xxxx.exe` (or latest stable)\n\n"
            "2. **Install with Additional Language Data:**\n"
            "   - Run the installer with administrator privileges.\n"
            "   - During component selection under **'Additional language data (download)'**, check:\n"
            "     - `[x] Tamil (tam)`\n"
            "     - `[x] Sinhala (sin)`\n"
            "     - `[x] English (eng)` (installed by default)\n"
            "   - Default installation directory: `C:\\Program Files\\Tesseract-OCR`\n\n"
            "3. **Add Tesseract to System PATH:**\n"
            "   - Open PowerShell as Administrator and run:\n"
            "     `[Environment]::SetEnvironmentVariable(\"Path\", $env:Path + \";C:\\Program Files\\Tesseract-OCR\", [EnvironmentVariableTarget]::Machine)`\n\n"
            "4. **Alternative: Manual Language Pack Download (.traineddata):**\n"
            "   - If Tesseract is already installed without Tamil or Sinhala:\n"
            "   - Download `tam.traineddata` and `sin.traineddata` from the official repository:\n"
            "     https://github.com/tesseract-ocr/tessdata_fast (Fast inference) OR\n"
            "     https://github.com/tesseract-ocr/tessdata_best (Higher accuracy)\n"
            "   - Copy the downloaded files into:\n"
            "     `C:\\Program Files\\Tesseract-OCR\\tessdata\\`\n\n"
            "5. **Python Dependencies:**\n"
            "   - Install Python wrapper and imaging libraries:\n"
            "     `pip install pytesseract Pillow opencv-python-headless`\n"
        )


def check_tesseract_environment() -> TesseractEnvironment:
    """Helper to instantiate and return current Tesseract environment diagnosis."""
    return TesseractEnvironment()
