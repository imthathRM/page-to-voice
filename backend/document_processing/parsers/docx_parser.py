"""
DOCX (Microsoft Word OpenXML) Document Parser.

Extracts paragraphs, headings, and table contents from .docx files.
Prefers `python-docx` if available, and seamlessly falls back to a robust
direct OpenXML / XML parser using Python's standard library `zipfile` and
`xml.etree.ElementTree`.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union
import xml.etree.ElementTree as ET
import zipfile

from ..base import BaseDocumentParser
from ..types import (
    CorruptedDocumentException,
    DocumentSection,
    ExtractionResult,
    ExtractionStatus,
)

# Optional dependency check
try:
    import docx
    HAS_PYTHON_DOCX = True
except ImportError:
    HAS_PYTHON_DOCX = False


class DOCXParser(BaseDocumentParser):
    """Parser for Microsoft Word (.docx) documents."""

    # OpenXML WordprocessingML namespace
    NAMESPACES = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    }

    @property
    def supported_formats(self) -> List[str]:
        return ["docx"]

    @property
    def parser_name(self) -> str:
        return "DOCXParser"

    def _parse_with_python_docx(
        self, path: Path
    ) -> Tuple[str, List[DocumentSection], List[str]]:
        """Extract content using python-docx library."""
        doc = docx.Document(str(path))
        sections: List[DocumentSection] = []
        all_text_parts: List[str] = []
        warnings: List[str] = []

        sec_idx = 1
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            style_name = para.style.name if para.style else None
            is_heading = bool(style_name and "Heading" in style_name)

            sections.append(
                DocumentSection(
                    index=sec_idx,
                    section_type="heading" if is_heading else "paragraph",
                    title=text if is_heading else None,
                    content=text,
                    metadata={"style": style_name or "Normal"},
                )
            )
            all_text_parts.append(text)
            sec_idx += 1

        # Also extract table text
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    row_text = " | ".join(row_cells)
                    sections.append(
                        DocumentSection(
                            index=sec_idx,
                            section_type="table_row",
                            content=row_text,
                            metadata={"type": "table_cell"},
                        )
                    )
                    all_text_parts.append(row_text)
                    sec_idx += 1

        full_text = "\n\n".join(all_text_parts)
        return full_text, sections, warnings

    def _parse_with_xml_fallback(
        self, path: Path
    ) -> Tuple[str, List[DocumentSection], List[str]]:
        """Extract content by parsing OpenXML zip archive directly."""
        sections: List[DocumentSection] = []
        all_text_parts: List[str] = []
        warnings: List[str] = []

        try:
            with zipfile.ZipFile(path, "r") as zf:
                if "word/document.xml" not in zf.namelist():
                    raise CorruptedDocumentException(
                        f"Malformed DOCX: 'word/document.xml' not found in {path.name}"
                    )
                xml_content = zf.read("word/document.xml")
        except zipfile.BadZipFile as e:
            raise CorruptedDocumentException(f"Corrupted or invalid DOCX archive {path.name}: {e}") from e

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise CorruptedDocumentException(f"Malformed XML in DOCX {path.name}: {e}") from e

        sec_idx = 1
        # Find all paragraph elements <w:p>
        for p in root.findall(".//w:p", self.NAMESPACES):
            # Check for heading style
            p_style = p.find(".//w:pPr/w:pStyle", self.NAMESPACES)
            style_val = (
                p_style.attrib.get(f"{{{self.NAMESPACES['w']}}}val", "")
                if p_style is not None
                else ""
            )
            is_heading = "Heading" in style_val or "heading" in style_val.lower()

            # Extract all text runs <w:t>
            text_nodes = p.findall(".//w:t", self.NAMESPACES)
            para_text = "".join(node.text for node in text_nodes if node.text)
            para_text = para_text.strip()

            if para_text:
                sections.append(
                    DocumentSection(
                        index=sec_idx,
                        section_type="heading" if is_heading else "paragraph",
                        title=para_text if is_heading else None,
                        content=para_text,
                        metadata={"style": style_val or "Normal"},
                    )
                )
                all_text_parts.append(para_text)
                sec_idx += 1

        full_text = "\n\n".join(all_text_parts)
        return full_text, sections, warnings

    def parse(self, file_path: Union[str, Path], **kwargs: Any) -> ExtractionResult:
        """Parse DOCX file and return structured text extraction result."""
        path = self.validate_file(file_path)

        warnings: List[str] = []
        try:
            if HAS_PYTHON_DOCX:
                try:
                    full_text, sections, p_warnings = self._parse_with_python_docx(path)
                    warnings.extend(p_warnings)
                    backend_used = "python-docx"
                except Exception as e:
                    # Fallback to direct XML on unexpected error
                    full_text, sections, xml_warnings = self._parse_with_xml_fallback(path)
                    warnings.extend(xml_warnings)
                    warnings.append(f"python-docx failed ({e}); successfully extracted via direct OpenXML parser.")
                    backend_used = "xml-fallback"
            else:
                full_text, sections, xml_warnings = self._parse_with_xml_fallback(path)
                warnings.extend(xml_warnings)
                backend_used = "xml-builtin"

        except CorruptedDocumentException:
            raise
        except Exception as e:
            raise CorruptedDocumentException(f"Failed to extract text from DOCX {path.name}: {e}") from e

        normalized = self.normalize_text(full_text)
        if not normalized:
            warnings.append("Document contains no readable text.")

        return ExtractionResult(
            text=normalized,
            file_name=path.name,
            file_type="docx",
            status=ExtractionStatus.SUCCESS,
            sections=sections,
            warnings=warnings,
            metadata={
                "parser_engine": backend_used,
                "paragraph_count": len(sections),
            },
        )
