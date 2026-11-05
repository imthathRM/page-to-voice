"""
PPTX (Microsoft PowerPoint OpenXML) Document Parser.

Extracts text slide-by-slide from .pptx presentations, preserving
slide boundaries, headings, and bullet points. Prefers `python-pptx`
if available, with automatic fallback to standard library OpenXML
zip/XML parsing.
"""

from __future__ import annotations

import re
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
    from pptx import Presentation
    HAS_PYTHON_PPTX = True
except ImportError:
    HAS_PYTHON_PPTX = False


class PPTXParser(BaseDocumentParser):
    """Parser for Microsoft PowerPoint (.pptx) presentations."""

    # DrawingML and PresentationML namespaces
    NAMESPACES = {
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }

    @property
    def supported_formats(self) -> List[str]:
        return ["pptx"]

    @property
    def parser_name(self) -> str:
        return "PPTXParser"

    def _parse_with_python_pptx(
        self, path: Path
    ) -> Tuple[str, List[DocumentSection], List[str]]:
        """Extract text slide-by-slide using python-pptx."""
        prs = Presentation(str(path))
        sections: List[DocumentSection] = []
        all_slide_texts: List[str] = []
        warnings: List[str] = []

        for idx, slide in enumerate(prs.slides, start=1):
            slide_parts: List[str] = []
            slide_title: Optional[str] = None

            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                shape_text = shape.text.strip()
                if not shape_text:
                    continue

                if shape == slide.shapes.title and not slide_title:
                    slide_title = shape_text

                slide_parts.append(shape_text)

            slide_text = "\n".join(slide_parts)
            if not slide_title and slide_parts:
                first_line = slide_parts[0].split("\n")[0]
                slide_title = first_line[:80]

            sections.append(
                DocumentSection(
                    index=idx,
                    section_type="slide",
                    title=slide_title or f"Slide {idx}",
                    content=slide_text,
                    metadata={"shape_count": len(slide.shapes)},
                )
            )
            if slide_text:
                all_slide_texts.append(f"--- Slide {idx}: {slide_title or ''} ---\n{slide_text}")

        full_text = "\n\n".join(all_slide_texts)
        return full_text, sections, warnings

    def _parse_with_xml_fallback(
        self, path: Path
    ) -> Tuple[str, List[DocumentSection], List[str]]:
        """Extract text slide-by-slide by directly inspecting OpenXML archive."""
        sections: List[DocumentSection] = []
        all_slide_texts: List[str] = []
        warnings: List[str] = []

        try:
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                # Find all slide XML files: ppt/slides/slide1.xml, slide2.xml, etc.
                slide_files = [n for n in names if re.match(r"^ppt/slides/slide\d+\.xml$", n)]

                if not slide_files and "ppt/presentation.xml" not in names:
                    raise CorruptedDocumentException(
                        f"Malformed PPTX: presentation components not found in {path.name}"
                    )

                # Sort slide files by slide index numerically
                def slide_key(filename: str) -> int:
                    m = re.search(r"slide(\d+)\.xml", filename)
                    return int(m.group(1)) if m else 0

                slide_files.sort(key=slide_key)

                for idx, s_file in enumerate(slide_files, start=1):
                    xml_content = zf.read(s_file)
                    try:
                        root = ET.fromstring(xml_content)
                    except ET.ParseError as pe:
                        warnings.append(f"Failed to parse slide {s_file}: {pe}")
                        continue

                    slide_lines: List[str] = []
                    slide_title: Optional[str] = None

                    # Locate all text bodies <p:txBody>
                    for tx_body in root.findall(".//p:txBody", self.NAMESPACES):
                        for p in tx_body.findall(".//a:p", self.NAMESPACES):
                            runs = p.findall(".//a:r/a:t", self.NAMESPACES)
                            p_text = "".join(r.text for r in runs if r.text).strip()
                            if p_text:
                                slide_lines.append(p_text)
                                if not slide_title:
                                    slide_title = p_text[:80]

                    content_str = "\n".join(slide_lines)
                    sections.append(
                        DocumentSection(
                            index=idx,
                            section_type="slide",
                            title=slide_title or f"Slide {idx}",
                            content=content_str,
                            metadata={"slide_xml": s_file},
                        )
                    )
                    if content_str:
                        all_slide_texts.append(f"--- Slide {idx}: {slide_title or ''} ---\n{content_str}")

        except zipfile.BadZipFile as e:
            raise CorruptedDocumentException(f"Corrupted or invalid PPTX archive {path.name}: {e}") from e

        full_text = "\n\n".join(all_slide_texts)
        return full_text, sections, warnings

    def parse(self, file_path: Union[str, Path], **kwargs: Any) -> ExtractionResult:
        """Parse PPTX file and return structured slide-by-slide text extraction."""
        path = self.validate_file(file_path)

        warnings: List[str] = []
        try:
            if HAS_PYTHON_PPTX:
                try:
                    full_text, sections, p_warnings = self._parse_with_python_pptx(path)
                    warnings.extend(p_warnings)
                    backend_used = "python-pptx"
                except Exception as e:
                    full_text, sections, x_warnings = self._parse_with_xml_fallback(path)
                    warnings.extend(x_warnings)
                    warnings.append(f"python-pptx failed ({e}); used direct OpenXML parser.")
                    backend_used = "xml-fallback"
            else:
                full_text, sections, x_warnings = self._parse_with_xml_fallback(path)
                warnings.extend(x_warnings)
                backend_used = "xml-builtin"

        except CorruptedDocumentException:
            raise
        except Exception as e:
            raise CorruptedDocumentException(f"Failed to extract text from PPTX {path.name}: {e}") from e

        normalized = self.normalize_text(full_text)
        if not normalized:
            warnings.append("Presentation contains no readable slide text.")

        return ExtractionResult(
            text=normalized,
            file_name=path.name,
            file_type="pptx",
            status=ExtractionStatus.SUCCESS,
            sections=sections,
            warnings=warnings,
            metadata={
                "parser_engine": backend_used,
                "slide_count": len(sections),
            },
        )
