"""
Document Parser Factory and Registry.

Provides a centralized, extensible factory for discovering, selecting,
and invoking format-specific parsers. Supports registration of new formats
without altering the core processing pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from .base import BaseDocumentParser
from .parsers import (
    DOCXParser,
    EPUBParser,
    PDFParser,
    PPTXParser,
    RTFParser,
    TXTParser,
)
from .types import (
    ExtractionResult,
    UnsupportedFileFormatException,
)


class DocumentParserFactory:
    """Central registry and factory for document parsers."""

    def __init__(self, register_defaults: bool = True) -> None:
        self._parsers: List[BaseDocumentParser] = []
        if register_defaults:
            self._register_default_parsers()

    def _register_default_parsers(self) -> None:
        """Register the six default document format parsers."""
        self.register(PDFParser())
        self.register(DOCXParser())
        self.register(TXTParser())
        self.register(PPTXParser())
        self.register(EPUBParser())
        self.register(RTFParser())

    def register(self, parser: BaseDocumentParser) -> None:
        """Register a new parser instance. Replaces existing parser for same extensions."""
        # Prepend to prioritize user-added parsers
        self._parsers.insert(0, parser)

    def get_supported_formats(self) -> List[str]:
        """Return a sorted list of all supported extensions (without dot)."""
        formats = set()
        for p in self._parsers:
            for fmt in p.supported_formats:
                formats.add(fmt.lower())
        return sorted(list(formats))

    def is_supported(self, file_path_or_ext: Union[str, Path]) -> bool:
        """Check if any registered parser supports the specified file or extension."""
        return any(parser.supports(file_path_or_ext) for parser in self._parsers)

    def get_parser(self, file_path_or_ext: Union[str, Path]) -> BaseDocumentParser:
        """Find and return the appropriate parser for a file or extension.

        Args:
            file_path_or_ext: File name, file path, or extension string.

        Returns:
            BaseDocumentParser: Matching parser instance.

        Raises:
            UnsupportedFileFormatException: If no registered parser handles the format.
        """
        for parser in self._parsers:
            if parser.supports(file_path_or_ext):
                return parser

        # If not found, extract extension for detailed error message
        if isinstance(file_path_or_ext, Path):
            ext = file_path_or_ext.suffix
        else:
            ext = Path(str(file_path_or_ext)).suffix or str(file_path_or_ext)

        raise UnsupportedFileFormatException(
            f"Unsupported document format '{ext}'. "
            f"Supported formats: {', '.join(self.get_supported_formats())}"
        )

    def parse_document(
        self, file_path: Union[str, Path], **kwargs: Any
    ) -> ExtractionResult:
        """High-level entry point to detect format and parse a document.

        Args:
            file_path: Path to the target document.
            **kwargs: Extra parameters passed to the selected parser.

        Returns:
            ExtractionResult: Standardized extraction structure.
        """
        parser = self.get_parser(file_path)
        return parser.parse(file_path, **kwargs)


# Global default factory instance
_default_factory = DocumentParserFactory()


def get_default_factory() -> DocumentParserFactory:
    """Return the global default DocumentParserFactory instance."""
    return _default_factory


def get_parser_for_file(file_path_or_ext: Union[str, Path]) -> BaseDocumentParser:
    """Convenience helper to get a parser from the default factory."""
    return _default_factory.get_parser(file_path_or_ext)


def parse_document(file_path: Union[str, Path], **kwargs: Any) -> ExtractionResult:
    """Convenience helper to parse a document using the default factory."""
    return _default_factory.parse_document(file_path, **kwargs)


def get_supported_formats() -> List[str]:
    """Convenience helper to retrieve supported file extensions."""
    return _default_factory.get_supported_formats()
