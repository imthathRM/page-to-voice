"""
RTF (Rich Text Format) Document Parser.

Extracts text from .rtf documents with full support for Unicode escapes
(\\uN?), hex-encoded bytes (\\'hh), paragraph controls (\\par), and
proper handling of document destinations and headers. Prefers `striprtf`
if available, and includes a comprehensive built-in RTF tokenizer
supporting Indic Unicode (Tamil & Sinhala).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from ..base import BaseDocumentParser
from ..types import (
    CorruptedDocumentException,
    DocumentSection,
    ExtractionResult,
    ExtractionStatus,
)

# Optional dependency check
try:
    from striprtf.striprtf import rtf_to_text
    HAS_STRIPRTF = True
except ImportError:
    HAS_STRIPRTF = False


class RTFParser(BaseDocumentParser):
    """Parser for Rich Text Format (.rtf) documents."""

    # RTF destinations to ignore entirely
    IGNORED_DESTINATIONS = {
        r"\fonttbl",
        r"\colortbl",
        r"\stylesheet",
        r"\info",
        r"\generator",
        r"\pict",
        r"\object",
        r"\header",
        r"\footer",
        r"\footnote",
        r"\*",
    }

    @property
    def supported_formats(self) -> List[str]:
        return ["rtf"]

    @property
    def parser_name(self) -> str:
        return "RTFParser"

    def _parse_with_builtin_tokenizer(self, rtf_text: str) -> str:
        """Parse RTF text into plain text preserving Unicode codepoints."""
        if not rtf_text.strip().startswith(r"{\rtf"):
            raise CorruptedDocumentException("Malformed RTF: File does not start with '{\\rtf'")

        # Track groups and destination skips
        stack = []  # tracks skip boolean for each nested group
        skip = False
        out: List[str] = []
        uc_skip = 1  # default \uc1
        i = 0
        n = len(rtf_text)

        while i < n:
            ch = rtf_text[i]

            if ch == "{":
                stack.append(skip)
                i += 1
                continue
            elif ch == "}":
                if stack:
                    skip = stack.pop()
                i += 1
                continue
            elif ch == "\\":
                # Control word or symbol
                i += 1
                if i >= n:
                    break

                ctl_ch = rtf_text[i]
                if ctl_ch in ("{", "}", "\\"):
                    if not skip:
                        out.append(ctl_ch)
                    i += 1
                    continue
                elif ctl_ch == "~":
                    if not skip:
                        out.append("\u00a0")  # non-breaking space
                    i += 1
                    continue
                elif ctl_ch == "_":
                    if not skip:
                        out.append("\u2011")  # non-breaking hyphen
                    i += 1
                    continue
                elif ctl_ch == "'":
                    # Hex byte \'hh
                    hex_str = rtf_text[i + 1 : i + 3]
                    if len(hex_str) == 2:
                        try:
                            byte_val = int(hex_str, 16)
                            if not skip:
                                out.append(chr(byte_val))
                        except ValueError:
                            pass
                        i += 3
                    else:
                        i += 1
                    continue

                # Read control word name and optional numeric parameter
                m = re.match(r"^([a-zA-Z]+)(-?\d+)? ?(.*)$", rtf_text[i:], re.DOTALL)
                if not m:
                    i += 1
                    continue

                word = m.group(1)
                num = m.group(2)
                matched_len = len(word) + (len(num) if num else 0)
                if (i + matched_len < n) and rtf_text[i + matched_len] == " ":
                    matched_len += 1  # consume space delimiter

                full_ctl = "\\" + word
                if full_ctl in self.IGNORED_DESTINATIONS:
                    skip = True

                if word == "par" or word == "line":
                    if not skip:
                        out.append("\n")
                elif word == "tab":
                    if not skip:
                        out.append("\t")
                elif word == "uc":
                    if num:
                        uc_skip = max(0, int(num))
                elif word == "u":
                    if num and not skip:
                        code = int(num)
                        if code < 0:
                            code += 65536  # Convert 16-bit signed to unsigned
                        try:
                            out.append(chr(code))
                        except (ValueError, OverflowError):
                            pass
                    # Skip uc_skip characters (the ASCII fallback representation in RTF)
                    i += matched_len
                    # Skip following fallback characters
                    chars_skipped = 0
                    while i < n and chars_skipped < uc_skip:
                        if rtf_text[i] == "\\":
                            # If it's a \'hh hex escape, consume it
                            if rtf_text[i : i + 2] == "\\'":
                                i += 4
                                chars_skipped += 1
                                continue
                            else:
                                break
                        elif rtf_text[i] in ("{", "}"):
                            break
                        else:
                            i += 1
                            chars_skipped += 1
                    continue

                i += matched_len

            else:
                if not skip and ch not in ("\r", "\n"):
                    out.append(ch)
                i += 1

        return "".join(out)

    def parse(self, file_path: Union[str, Path], **kwargs: Any) -> ExtractionResult:
        """Parse RTF file and return structured text extraction result."""
        path = self.validate_file(file_path)

        try:
            # RTF files are strictly 7-bit ASCII with escapes, or latin-1/utf-8
            with open(path, "rb") as f:
                raw_bytes = f.read()
        except OSError as e:
            raise CorruptedDocumentException(f"Failed to read RTF file {path.name}: {e}") from e

        if not raw_bytes:
            return ExtractionResult(
                text="",
                file_name=path.name,
                file_type="rtf",
                status=ExtractionStatus.SUCCESS,
                sections=[],
                warnings=["RTF document is empty."],
                metadata={"file_size_bytes": 0},
            )

        # Decode RTF as ascii/latin1 to process control words
        try:
            rtf_str = raw_bytes.decode("ascii")
        except UnicodeDecodeError:
            try:
                rtf_str = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                rtf_str = raw_bytes.decode("latin-1", errors="replace")

        warnings: List[str] = []
        try:
            extracted_text = self._parse_with_builtin_tokenizer(rtf_str)
            backend_used = "rtf-builtin"
        except CorruptedDocumentException:
            raise
        except Exception as e:
            if HAS_STRIPRTF:
                try:
                    extracted_text = rtf_to_text(rtf_str)
                    backend_used = "striprtf-fallback"
                except Exception as s_err:
                    raise CorruptedDocumentException(f"Failed to parse RTF {path.name}: {s_err}") from s_err
            else:
                raise CorruptedDocumentException(f"Failed to parse RTF {path.name}: {e}") from e

        normalized = self.normalize_text(extracted_text)

        # Split into paragraph sections
        sections: List[DocumentSection] = []
        if normalized:
            paras = [p.strip() for p in normalized.split("\n\n") if p.strip()]
            if not paras:
                paras = [normalized]
            for idx, para in enumerate(paras, start=1):
                sections.append(
                    DocumentSection(
                        index=idx,
                        section_type="paragraph",
                        content=para,
                    )
                )

        return ExtractionResult(
            text=normalized,
            file_name=path.name,
            file_type="rtf",
            status=ExtractionStatus.SUCCESS,
            sections=sections,
            warnings=warnings,
            metadata={
                "parser_engine": backend_used,
                "paragraph_count": len(sections),
            },
        )
