"""
Page to Voice - Document Processing Package.

Provides a unified interface, format-specific parsers, and extensible
factory architecture for extracting structured text from PDF, DOCX, TXT,
PPTX, EPUB, and RTF documents with multilingual Unicode support.
"""

from .base import BaseDocumentParser
from .factory import (
    DocumentParserFactory,
    get_default_factory,
    get_parser_for_file,
    get_supported_formats,
    parse_document,
)
from .parsers import (
    DOCXParser,
    EPUBParser,
    PDFParser,
    PPTXParser,
    RTFParser,
    TXTParser,
)
from .types import (
    CorruptedDocumentException,
    DocumentProcessingError,
    DocumentSection,
    EmptyDocumentException,
    ExtractionResult,
    ExtractionStatus,
    FileAccessError,
    SupportedFormat,
    UnsupportedFileFormatException,
)

__all__ = [
    # Types & Models
    "DocumentSection",
    "ExtractionResult",
    "ExtractionStatus",
    "SupportedFormat",
    # Exceptions
    "DocumentProcessingError",
    "UnsupportedFileFormatException",
    "CorruptedDocumentException",
    "EmptyDocumentException",
    "FileAccessError",
    # Interfaces & Factory
    "BaseDocumentParser",
    "DocumentParserFactory",
    "get_default_factory",
    "get_parser_for_file",
    "get_supported_formats",
    "parse_document",
    # Parsers
    "PDFParser",
    "DOCXParser",
    "TXTParser",
    "PPTXParser",
    "EPUBParser",
    "RTFParser",
]
