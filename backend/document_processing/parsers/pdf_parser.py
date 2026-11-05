"""
PDF (Portable Document Format) Document Parser.

Extracts text page-by-page from .pdf documents, preserving page
boundaries, layout structure, and Unicode characters (English, Tamil,
Sinhala). Prefers `PyMuPDF` (fitz) if installed, and includes a
pure-Python stream / operator fallback extractor.
"""

from __future__ import annotations

import binascii
import re
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union
import zlib

from ..base import BaseDocumentParser
from ..types import (
    CorruptedDocumentException,
    DocumentSection,
    ExtractionResult,
    ExtractionStatus,
)

# Optional dependency check: PyMuPDF
try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


class PDFParser(BaseDocumentParser):
    """Parser for Portable Document Format (.pdf) documents."""

    @property
    def supported_formats(self) -> List[str]:
        return ["pdf"]

    @property
    def parser_name(self) -> str:
        return "PDFParser"

    def _parse_with_pymupdf(
        self, path: Path
    ) -> Tuple[str, List[DocumentSection], List[str], int]:
        """Extract text page-by-page using PyMuPDF (fitz)."""
        sections: List[DocumentSection] = []
        page_texts: List[str] = []
        warnings: List[str] = []

        try:
            doc = fitz.open(str(path))
        except Exception as e:
            raise CorruptedDocumentException(f"PyMuPDF failed to open PDF {path.name}: {e}") from e

        if doc.is_encrypted:
            warnings.append("PDF is password-protected or encrypted; content may be inaccessible.")

        page_count = len(doc)
        for page_idx in range(page_count):
            page = doc[page_idx]
            text = page.get_text("text").strip()
            page_num = page_idx + 1

            sections.append(
                DocumentSection(
                    index=page_num,
                    section_type="page",
                    title=f"Page {page_num}",
                    content=text,
                    metadata={"rect": list(page.rect)},
                )
            )
            if text:
                page_texts.append(f"--- Page {page_num} ---\n{text}")

        full_text = "\n\n".join(page_texts)
        doc.close()
        return full_text, sections, warnings, page_count

    def _decode_pdf_string(self, s: str) -> str:
        """Decode a PDF literal or hex text string, handling UTF-16BE if present."""
        s = s.strip()
        # Check if hex string: <...>
        if s.startswith("<") and s.endswith(">"):
            hex_data = s[1:-1].strip()
            # If odd length, append trailing zero per PDF spec
            if len(hex_data) % 2 != 0:
                hex_data += "0"
            try:
                raw_bytes = binascii.unhexlify(hex_data)
                # Check for UTF-16BE BOM (\xfe\xff)
                if raw_bytes.startswith(b"\xfe\xff"):
                    return raw_bytes[2:].decode("utf-16-be", errors="replace")
                # Try UTF-8
                try:
                    return raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    return raw_bytes.decode("latin-1", errors="replace")
            except Exception:
                return ""

        # Literal string (escaped)
        # Unescape standard PDF octal \ooo and special chars
        res = []
        i = 0
        n = len(s)
        while i < n:
            if s[i] == "\\" and i + 1 < n:
                nxt = s[i + 1]
                if nxt == "n":
                    res.append("\n")
                    i += 2
                elif nxt == "r":
                    res.append("\r")
                    i += 2
                elif nxt == "t":
                    res.append("\t")
                    i += 2
                elif nxt in ("(", ")", "\\"):
                    res.append(nxt)
                    i += 2
                elif nxt.isdigit() and i + 3 <= n:
                    # Octal escape
                    oct_digits = s[i + 1 : i + 4]
                    try:
                        res.append(chr(int(oct_digits, 8)))
                        i += 4
                    except ValueError:
                        res.append(nxt)
                        i += 2
                else:
                    res.append(nxt)
                    i += 2
            else:
                res.append(s[i])
                i += 1
        return "".join(res)

    def _extract_text_from_stream(self, stream_data: bytes) -> str:
        """Parse PDF content stream for BT...ET text blocks and Tj/TJ operators."""
        try:
            stream_str = stream_data.decode("latin-1")
        except UnicodeDecodeError:
            stream_str = stream_data.decode("utf-8", errors="replace")

        text_pieces: List[str] = []
        # Find all BT ... ET text blocks
        bt_blocks = re.findall(r"BT(.*?)ET", stream_str, re.DOTALL)
        for block in bt_blocks:
            # Match Tj operators: (text) Tj or <hex> Tj
            tj_matches = re.findall(r"(\([^\)]*\)|<[0-9a-fA-F\s]+>)\s*Tj", block)
            for m in tj_matches:
                inner = m[1:-1] if m.startswith("(") else m
                decoded = self._decode_pdf_string(inner if not m.startswith("(") else f"({inner})")
                if decoded:
                    text_pieces.append(decoded)

            # Match TJ operators: [ ... ] TJ
            tj_array_matches = re.findall(r"\[(.*?)\]\s*TJ", block)
            for arr in tj_array_matches:
                items = re.findall(r"(\([^\)]*\)|<[0-9a-fA-F\s]+>)", arr)
                for item in items:
                    decoded = self._decode_pdf_string(item)
                    if decoded:
                        text_pieces.append(decoded)

        return " ".join(text_pieces)

    def _parse_with_pdf_fallback(
        self, path: Path
    ) -> Tuple[str, List[DocumentSection], List[str], int]:
        """Pure Python fallback parser for uncompressed and flate-compressed PDF streams."""
        sections: List[DocumentSection] = []
        all_texts: List[str] = []
        warnings: List[str] = []

        try:
            with open(path, "rb") as f:
                raw_bytes = f.read()
        except OSError as e:
            raise CorruptedDocumentException(f"Failed to read PDF file {path.name}: {e}") from e

        if not raw_bytes.startswith(b"%PDF-"):
            raise CorruptedDocumentException(f"Malformed PDF: header '%PDF-' missing in {path.name}")

        # Check for mandatory PDF trailer / EOF marker to catch truncated files
        if b"%%EOF" not in raw_bytes[-2048:]:
            raise CorruptedDocumentException(f"Malformed PDF: missing %%EOF marker (truncated file) in {path.name}")

        # Check for catalog or pages structure
        if b"/Catalog" not in raw_bytes and b"/Pages" not in raw_bytes:
            raise CorruptedDocumentException(f"Malformed PDF: document lacks catalog or pages dictionary in {path.name}")

        # Find stream ... endstream blocks
        stream_matches = list(re.finditer(b"stream\r?\n(.*?)\r?\nendstream", raw_bytes, re.DOTALL))
        page_idx = 1

        for sm in stream_matches:
            stream_content = sm.group(1)
            # Try FlateDecode decompress
            try:
                decompressed = zlib.decompress(stream_content)
            except zlib.error:
                # Raw uncompressed stream
                decompressed = stream_content

            extracted = self._extract_text_from_stream(decompressed)
            extracted = extracted.strip()
            if extracted:
                sections.append(
                    DocumentSection(
                        index=page_idx,
                        section_type="page",
                        title=f"Page {page_idx}",
                        content=extracted,
                    )
                )
                all_texts.append(f"--- Page {page_idx} ---\n{extracted}")
                page_idx += 1

        if not sections:
            # If no stream text found, scan for literal strings in the whole document
            raw_str = raw_bytes.decode("latin-1", errors="replace")
            literal_texts = re.findall(r"\(([\w\s\.,!\?'-]{4,})\)\s*Tj", raw_str)
            if literal_texts:
                combined = " ".join(literal_texts).strip()
                sections.append(
                    DocumentSection(
                        index=1,
                        section_type="page",
                        title="Page 1",
                        content=combined,
                    )
                )
                all_texts.append(combined)

        full_text = "\n\n".join(all_texts)
        page_count = max(len(sections), 1)
        return full_text, sections, warnings, page_count

    def parse(self, file_path: Union[str, Path], **kwargs: Any) -> ExtractionResult:
        """Parse PDF document and return structured page-by-page text."""
        path = self.validate_file(file_path)

        warnings: List[str] = []
        try:
            if HAS_PYMUPDF:
                try:
                    full_text, sections, p_warnings, page_count = self._parse_with_pymupdf(path)
                    warnings.extend(p_warnings)
                    backend_used = "PyMuPDF"
                except Exception as e:
                    full_text, sections, f_warnings, page_count = self._parse_with_pdf_fallback(path)
                    warnings.extend(f_warnings)
                    warnings.append(f"PyMuPDF failed ({e}); used pure-Python stream parser.")
                    backend_used = "pdf-stream-fallback"
            else:
                full_text, sections, f_warnings, page_count = self._parse_with_pdf_fallback(path)
                warnings.extend(f_warnings)
                backend_used = "pdf-stream-builtin"

        except CorruptedDocumentException:
            raise
        except Exception as e:
            raise CorruptedDocumentException(f"Failed to extract text from PDF {path.name}: {e}") from e

        normalized = self.normalize_text(full_text)
        if not normalized:
            warnings.append("PDF contains no readable text content.")

        return ExtractionResult(
            text=normalized,
            file_name=path.name,
            file_type="pdf",
            status=ExtractionStatus.SUCCESS,
            sections=sections,
            warnings=warnings,
            metadata={
                "parser_engine": backend_used,
                "page_count": page_count,
            },
        )
