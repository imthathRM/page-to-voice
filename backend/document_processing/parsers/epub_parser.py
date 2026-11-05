"""
EPUB (Electronic Publication) Document Parser.

Extracts chapter-by-chapter text from .epub digital books, preserving
reading order via OPF spine definitions and chapter headings. Prefers
`ebooklib` if available, and seamlessly falls back to standard zipfile
and HTML / XHTML parsing (using BeautifulSoup or html.parser).
"""

from __future__ import annotations

import posixpath
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
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
    import ebooklib
    from ebooklib import epub
    HAS_EBOOKLIB = True
except ImportError:
    HAS_EBOOKLIB = False

# HTML parser check
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


class EPUBParser(BaseDocumentParser):
    """Parser for EPUB digital book publications."""

    @property
    def supported_formats(self) -> List[str]:
        return ["epub"]

    @property
    def parser_name(self) -> str:
        return "EPUBParser"

    def _html_to_text(self, html_bytes: bytes) -> Tuple[str, Optional[str]]:
        """Extract clean text and heading from HTML/XHTML bytes."""
        title: Optional[str] = None
        if HAS_BS4:
            soup = BeautifulSoup(html_bytes, "html.parser")
            # Extract title if present
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            elif soup.find(["h1", "h2"]):
                h_tag = soup.find(["h1", "h2"])
                if h_tag and h_tag.string:
                    title = h_tag.string.strip()

            # Remove scripts and styles
            for elem in soup(["script", "style", "meta", "link"]):
                elem.decompose()

            text = soup.get_text(separator="\n\n")
            cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
            return "\n\n".join(cleaned_lines), title
        else:
            # Fallback simple tag stripper
            decoded = html_bytes.decode("utf-8", errors="replace")
            import re
            # Extract title
            m = re.search(r"<title[^>]*>(.*?)</title>", decoded, re.IGNORECASE | re.DOTALL)
            if m:
                title = m.group(1).strip()
            # Strip tags
            no_tags = re.sub(r"<[^>]+>", "\n", decoded)
            lines = [l.strip() for l in no_tags.splitlines() if l.strip()]
            return "\n\n".join(lines), title

    def _parse_with_ebooklib(
        self, path: Path
    ) -> Tuple[str, List[DocumentSection], List[str]]:
        """Extract chapters using ebooklib."""
        book = epub.read_epub(str(path))
        sections: List[DocumentSection] = []
        all_texts: List[str] = []
        warnings: List[str] = []

        sec_idx = 1
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            content_bytes = item.get_content()
            chapter_text, detected_title = self._html_to_text(content_bytes)

            if not chapter_text:
                continue

            item_title = item.get_name()
            title = detected_title or item_title

            sections.append(
                DocumentSection(
                    index=sec_idx,
                    section_type="chapter",
                    title=title,
                    content=chapter_text,
                    metadata={"item_name": item.get_name()},
                )
            )
            all_texts.append(f"=== {title} ===\n{chapter_text}")
            sec_idx += 1

        full_text = "\n\n".join(all_texts)
        return full_text, sections, warnings

    def _parse_with_zip_fallback(
        self, path: Path
    ) -> Tuple[str, List[DocumentSection], List[str]]:
        """Parse EPUB package directly via standard zipfile and OPF spine."""
        sections: List[DocumentSection] = []
        all_texts: List[str] = []
        warnings: List[str] = []

        try:
            with zipfile.ZipFile(path, "r") as zf:
                # 1. Locate container.xml
                if "META-INF/container.xml" not in zf.namelist():
                    raise CorruptedDocumentException(
                        f"Malformed EPUB: missing 'META-INF/container.xml' in {path.name}"
                    )

                container_xml = zf.read("META-INF/container.xml")
                try:
                    c_root = ET.fromstring(container_xml)
                except ET.ParseError as e:
                    raise CorruptedDocumentException(f"Invalid container.xml in EPUB {path.name}: {e}") from e

                # Find rootfile
                rootfile_elem = c_root.find(".//{*}rootfile")
                if rootfile_elem is None or "full-path" not in rootfile_elem.attrib:
                    raise CorruptedDocumentException(
                        f"Malformed EPUB: no rootfile full-path found in container.xml for {path.name}"
                    )

                opf_path = rootfile_elem.attrib["full-path"]
                if opf_path not in zf.namelist():
                    raise CorruptedDocumentException(
                        f"Malformed EPUB: package file '{opf_path}' not found in archive"
                    )

                opf_dir = posixpath.dirname(opf_path)
                opf_xml = zf.read(opf_path)

                try:
                    opf_root = ET.fromstring(opf_xml)
                except ET.ParseError as e:
                    raise CorruptedDocumentException(f"Invalid OPF XML in {path.name}: {e}") from e

                # 2. Parse manifest (id -> href)
                manifest: Dict[str, str] = {}
                for item in opf_root.findall(".//{*}manifest/{*}item"):
                    i_id = item.attrib.get("id")
                    i_href = item.attrib.get("href")
                    if i_id and i_href:
                        # Normalize href relative to opf directory
                        full_href = posixpath.normpath(posixpath.join(opf_dir, i_href)) if opf_dir else i_href
                        manifest[i_id] = full_href

                # 3. Parse spine (reading order of idrefs)
                spine_items: List[str] = []
                for itemref in opf_root.findall(".//{*}spine/{*}itemref"):
                    idref = itemref.attrib.get("idref")
                    if idref and idref in manifest:
                        spine_items.append(manifest[idref])

                # If spine is empty, fallback to all html/xhtml files in manifest
                if not spine_items:
                    spine_items = [
                        href for href in manifest.values()
                        if href.endswith((".xhtml", ".html", ".htm", ".xml"))
                    ]

                # 4. Extract content for each spine item in sequence
                sec_idx = 1
                for item_path in spine_items:
                    if item_path not in zf.namelist():
                        continue

                    raw_html = zf.read(item_path)
                    chap_text, detected_title = self._html_to_text(raw_html)

                    if not chap_text:
                        continue

                    title = detected_title or f"Chapter {sec_idx}"
                    sections.append(
                        DocumentSection(
                            index=sec_idx,
                            section_type="chapter",
                            title=title,
                            content=chap_text,
                            metadata={"file_path": item_path},
                        )
                    )
                    all_texts.append(f"=== {title} ===\n{chap_text}")
                    sec_idx += 1

        except zipfile.BadZipFile as e:
            raise CorruptedDocumentException(f"Corrupted or invalid EPUB archive {path.name}: {e}") from e

        full_text = "\n\n".join(all_texts)
        return full_text, sections, warnings

    def parse(self, file_path: Union[str, Path], **kwargs: Any) -> ExtractionResult:
        """Parse EPUB digital book and return chapter-by-chapter extracted text."""
        path = self.validate_file(file_path)

        warnings: List[str] = []
        try:
            if HAS_EBOOKLIB:
                try:
                    full_text, sections, eb_warnings = self._parse_with_ebooklib(path)
                    warnings.extend(eb_warnings)
                    backend_used = "ebooklib"
                except Exception as e:
                    full_text, sections, z_warnings = self._parse_with_zip_fallback(path)
                    warnings.extend(z_warnings)
                    warnings.append(f"ebooklib failed ({e}); used direct OPF spine zip parser.")
                    backend_used = "epub-zip-fallback"
            else:
                full_text, sections, z_warnings = self._parse_with_zip_fallback(path)
                warnings.extend(z_warnings)
                backend_used = "epub-zip-builtin"

        except CorruptedDocumentException:
            raise
        except Exception as e:
            raise CorruptedDocumentException(f"Failed to extract text from EPUB {path.name}: {e}") from e

        normalized = self.normalize_text(full_text)
        if not normalized:
            warnings.append("EPUB publication contains no readable text content.")

        return ExtractionResult(
            text=normalized,
            file_name=path.name,
            file_type="epub",
            status=ExtractionStatus.SUCCESS,
            sections=sections,
            warnings=warnings,
            metadata={
                "parser_engine": backend_used,
                "chapter_count": len(sections),
            },
        )
