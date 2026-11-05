"""
Document Processing Type Definitions, Data Classes, and Exceptions.

Provides standardized data models, status enumerations, and exceptions
for all document parsers across the Page to Voice platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ExtractionStatus(str, Enum):
    """Status of the document extraction process."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class SupportedFormat(str, Enum):
    """Document formats supported by the parser suite."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    PPTX = "pptx"
    EPUB = "epub"
    RTF = "rtf"

    @classmethod
    def is_supported(cls, ext: str) -> bool:
        """Check if an extension (with or without leading dot) is supported."""
        normalized = ext.lower().lstrip(".")
        return normalized in [f.value for f in cls]


@dataclass
class DocumentSection:
    """Represents a structural division of a document (page, slide, chapter, etc.).

    Attributes:
        index: 1-based sequential section index.
        section_type: Type of section ("page", "slide", "chapter", "paragraph", "section").
        content: Extracted textual content of this section.
        title: Optional section heading or title.
        metadata: Format-specific metadata (dimensions, word count, notes, etc.).
    """
    index: int
    section_type: str = "paragraph"
    content: str = ""
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert section to a JSON-serializable dictionary."""
        return {
            "index": self.index,
            "section_type": self.section_type,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata,
        }


@dataclass
class ExtractionResult:
    """Standardized output structure for document parsers.

    Attributes:
        text: Complete extracted and normalized text from the document.
        file_name: Name or path of the parsed document.
        file_type: Extension or format identifier (e.g. "pdf", "docx").
        status: Extraction outcome (SUCCESS, PARTIAL, FAILED).
        sections: Breakdown of sections (pages, slides, chapters, paragraphs).
        warnings: Non-fatal warnings encountered during extraction.
        error: Fatal error message if extraction failed.
        metadata: Global document metadata (page count, char count, encoding, etc.).
    """
    text: str = ""
    file_name: str = ""
    file_type: str = ""
    status: ExtractionStatus = ExtractionStatus.SUCCESS
    sections: List[DocumentSection] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Populate basic statistical metadata if not provided."""
        if "char_count" not in self.metadata:
            self.metadata["char_count"] = len(self.text)
        if "word_count" not in self.metadata:
            self.metadata["word_count"] = len(self.text.split()) if self.text else 0
        if "section_count" not in self.metadata:
            self.metadata["section_count"] = len(self.sections)

    @property
    def is_success(self) -> bool:
        """Return True if extraction was successful."""
        return self.status == ExtractionStatus.SUCCESS

    @property
    def has_warnings(self) -> bool:
        """Return True if non-fatal warnings occurred."""
        return len(self.warnings) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a JSON-serializable dictionary."""
        return {
            "text": self.text,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "status": self.status.value,
            "sections": [s.to_dict() for s in self.sections],
            "warnings": self.warnings,
            "error": self.error,
            "metadata": self.metadata,
        }


# ============================================================================
# Exception Hierarchy
# ============================================================================

class DocumentProcessingError(Exception):
    """Base exception for all document processing errors."""
    pass


class UnsupportedFileFormatException(DocumentProcessingError):
    """Raised when an unrecognized or unsupported file format is encountered."""
    pass


class CorruptedDocumentException(DocumentProcessingError):
    """Raised when a document is damaged, malformed, or cannot be read."""
    pass


class EmptyDocumentException(DocumentProcessingError):
    """Raised or warned when a document contains no extractable content."""
    pass


class FileAccessError(DocumentProcessingError):
    """Raised when a file cannot be located, opened, or read from disk."""
    pass
