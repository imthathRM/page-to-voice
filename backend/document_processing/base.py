"""
Base Document Parser Abstract Interface.

Defines the contract that every document format parser must implement,
ensuring consistent behaviour, validation, error handling, and output.
"""

from __future__ import annotations

import io
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .types import (
    CorruptedDocumentException,
    DocumentSection,
    ExtractionResult,
    ExtractionStatus,
    FileAccessError,
    UnsupportedFileFormatException,
)


class BaseDocumentParser(ABC):
    """Abstract base class for all document format parsers.

    Subclasses must implement:
        - supported_formats: List of supported file extensions without leading dot.
        - parser_name: Human-readable name of the parser.
        - parse: Main text extraction method.
    """

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """List of file extensions supported by this parser (lowercase, no dot)."""
        pass

    @property
    @abstractmethod
    def parser_name(self) -> str:
        """Name of the parser implementation."""
        pass

    def supports(self, file_path_or_ext: Union[str, Path]) -> bool:
        """Check whether this parser can handle the given file or extension.

        Args:
            file_path_or_ext: File name, file path, or extension string.

        Returns:
            bool: True if supported, False otherwise.
        """
        if not file_path_or_ext:
            return False

        if isinstance(file_path_or_ext, Path):
            ext = file_path_or_ext.suffix.lower().lstrip(".")
        else:
            str_path = str(file_path_or_ext).strip()
            # If input is already just an extension like "pdf" or ".pdf"
            if "." in str_path:
                ext = str_path.rsplit(".", 1)[-1].lower()
            else:
                ext = str_path.lower()

        return ext in [fmt.lower() for fmt in self.supported_formats]

    def validate_file(self, file_path: Union[str, Path]) -> Path:
        """Validate that a target file exists, is a regular file, and can be read.

        Args:
            file_path: Path to the document.

        Returns:
            Path: Resolved Path object.

        Raises:
            FileAccessError: If the file does not exist, is a directory, or cannot be accessed.
            UnsupportedFileFormatException: If the file format is not supported by this parser.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileAccessError(f"Document file does not exist: {path}")
        if not path.is_file():
            raise FileAccessError(f"Target path is not a regular file: {path}")
        if not os.access(path, os.R_OK):
            raise FileAccessError(f"Permission denied: cannot read file at {path}")

        if not self.supports(path):
            raise UnsupportedFileFormatException(
                f"Parser '{self.parser_name}' does not support file: {path.name} "
                f"(expected one of {self.supported_formats})"
            )

        return path

    @abstractmethod
    def parse(self, file_path: Union[str, Path], **kwargs: Any) -> ExtractionResult:
        """Extract text from the specified document.

        Args:
            file_path: Path to the target document.
            **kwargs: Format-specific parser options.

        Returns:
            ExtractionResult: Standardized extraction structure.

        Raises:
            FileAccessError: If the file cannot be accessed.
            UnsupportedFileFormatException: If the file extension is not supported.
            CorruptedDocumentException: If the file is malformed or damaged.
        """
        pass

    def parse_bytes(
        self,
        content: bytes,
        file_name: str = "document",
        **kwargs: Any,
    ) -> ExtractionResult:
        """Parse document content provided as raw bytes (e.g. from an upload).

        Creates a secure temporary file, executes parse(), and cleans up afterwards.

        Args:
            content: Raw byte content of the file.
            file_name: Original file name (used to infer extension).
            **kwargs: Format-specific parser options.

        Returns:
            ExtractionResult: Standardized extraction structure.
        """
        ext = Path(file_name).suffix
        if not ext and self.supported_formats:
            ext = f".{self.supported_formats[0]}"

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            result = self.parse(tmp_path, **kwargs)
            result.file_name = file_name
            return result
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    @staticmethod
    def normalize_text(text: str) -> str:
        """Clean and normalize extracted text string.

        Standardizes line endings to Unix style, strips leading/trailing
        whitespace, and cleans redundant null bytes.
        """
        if not text:
            return ""
        # Remove null bytes or invalid control chars
        cleaned = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
        return cleaned.strip()
