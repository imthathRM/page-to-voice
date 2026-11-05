"""
Plain Text Document Parser.

Robustly handles text files encoded in UTF-8, UTF-8 with BOM, UTF-16,
and legacy single-byte encodings (CP1252/Latin-1) with defensive fallbacks.
Preserves Unicode scripts (English, Tamil, Sinhala) and special characters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Tuple, Union

from ..base import BaseDocumentParser
from ..types import (
    CorruptedDocumentException,
    DocumentSection,
    ExtractionResult,
    ExtractionStatus,
)


class TXTParser(BaseDocumentParser):
    """Parser for plain text (.txt) documents."""

    # Encodings attempted in sequence
    ENCODING_CANDIDATES = [
        "utf-8-sig",
        "utf-8",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "cp1252",
        "latin-1",
    ]

    @property
    def supported_formats(self) -> List[str]:
        return ["txt"]

    @property
    def parser_name(self) -> str:
        return "TXTParser"

    def _decode_bytes(self, raw_bytes: bytes) -> Tuple[str, str, List[str]]:
        """Decode raw bytes into a string trying candidate encodings safely."""
        warnings: List[str] = []

        if not raw_bytes:
            return "", "utf-8", ["Document is empty."]

        for enc in self.ENCODING_CANDIDATES:
            try:
                decoded = raw_bytes.decode(enc)
                return decoded, enc, warnings
            except (UnicodeDecodeError, LookupError):
                continue

        # Fallback to UTF-8 with character replacement
        warnings.append(
            "File encoding could not be determined strictly. "
            "Decoded with utf-8 using replacement characters for invalid bytes."
        )
        decoded = raw_bytes.decode("utf-8", errors="replace")
        return decoded, "utf-8-replace", warnings

    def parse(self, file_path: Union[str, Path], **kwargs: Any) -> ExtractionResult:
        """Parse text file and return standardized extraction result."""
        path = self.validate_file(file_path)

        try:
            with open(path, "rb") as f:
                raw_bytes = f.read()
        except OSError as e:
            raise CorruptedDocumentException(f"Failed to read text file {path.name}: {e}") from e

        raw_text, used_encoding, warnings = self._decode_bytes(raw_bytes)
        normalized = self.normalize_text(raw_text)

        # Build sections by splitting on multiple newlines (paragraphs)
        sections: List[DocumentSection] = []
        if normalized:
            # Paragraph split
            paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [normalized]

            for idx, para in enumerate(paragraphs, start=1):
                sections.append(
                    DocumentSection(
                        index=idx,
                        section_type="paragraph",
                        content=para,
                        metadata={"line_count": para.count("\n") + 1},
                    )
                )

        status = ExtractionStatus.SUCCESS
        if not normalized and raw_bytes:
            warnings.append("Document contained only non-printable or whitespace characters.")

        return ExtractionResult(
            text=normalized,
            file_name=path.name,
            file_type="txt",
            status=status,
            sections=sections,
            warnings=warnings,
            metadata={
                "detected_encoding": used_encoding,
                "file_size_bytes": len(raw_bytes),
                "paragraph_count": len(sections),
            },
        )
