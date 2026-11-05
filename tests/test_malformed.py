"""
Automated Tests for Malformed, Damaged, and Corrupted Documents.

Verifies:
- Corrupted PDF files are caught and raise CorruptedDocumentException.
- Corrupted DOCX files are caught safely.
- Corrupted PPTX files are caught safely.
- Corrupted EPUB files are caught safely.
- Corrupted RTF files are caught safely.
- One corrupted document does not crash the application process.
- Meaningful error messages are included with exceptions.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

# Ensure backend is in path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from document_processing import (
    CorruptedDocumentException,
    DOCXParser,
    DocumentProcessingError,
    EPUBParser,
    FileAccessError,
    PDFParser,
    PPTXParser,
    RTFParser,
    TXTParser,
    parse_document,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
MALFORMED_DIR = FIXTURES_DIR / "malformed"


class TestMalformedDocuments(unittest.TestCase):
    """Test suite for corrupted and invalid document fixtures."""

    def test_corrupted_pdf_file(self) -> None:
        """Verify invalid.pdf raises CorruptedDocumentException with meaningful message."""
        path = MALFORMED_DIR / "invalid.pdf"
        with self.assertRaises(CorruptedDocumentException) as ctx:
            parse_document(path)
        self.assertIn("PDF", str(ctx.exception))

    def test_corrupted_docx_file(self) -> None:
        """Verify invalid.docx raises CorruptedDocumentException."""
        path = MALFORMED_DIR / "invalid.docx"
        with self.assertRaises(CorruptedDocumentException) as ctx:
            parse_document(path)
        self.assertIn("DOCX", str(ctx.exception))

    def test_corrupted_pptx_file(self) -> None:
        """Verify invalid.pptx raises CorruptedDocumentException."""
        path = MALFORMED_DIR / "invalid.pptx"
        with self.assertRaises(CorruptedDocumentException) as ctx:
            parse_document(path)
        self.assertIn("PPTX", str(ctx.exception))

    def test_corrupted_epub_file(self) -> None:
        """Verify invalid.epub raises CorruptedDocumentException."""
        path = MALFORMED_DIR / "invalid.epub"
        with self.assertRaises(CorruptedDocumentException) as ctx:
            parse_document(path)
        self.assertIn("EPUB", str(ctx.exception))

    def test_corrupted_rtf_file(self) -> None:
        """Verify invalid.rtf raises CorruptedDocumentException."""
        path = MALFORMED_DIR / "invalid.rtf"
        with self.assertRaises(CorruptedDocumentException) as ctx:
            parse_document(path)
        self.assertIn("RTF", str(ctx.exception))

    def test_batch_processing_resilience(self) -> None:
        """Verify that encountering corrupted files in a batch does not crash subsequent processing."""
        mixed_batch = [
            MALFORMED_DIR / "invalid.pdf",
            FIXTURES_DIR / "documents" / "sample.txt",
            MALFORMED_DIR / "invalid.docx",
            FIXTURES_DIR / "documents" / "sample.rtf",
            MALFORMED_DIR / "invalid.pptx",
        ]

        success_count = 0
        error_count = 0

        for doc_path in mixed_batch:
            try:
                res = parse_document(doc_path)
                if res.is_success:
                    success_count += 1
            except DocumentProcessingError:
                error_count += 1

        self.assertEqual(success_count, 2)
        self.assertEqual(error_count, 3)

    def test_random_binary_garbage_handling(self) -> None:
        """Verify arbitrary binary garbage in place of document files raises clean exceptions."""
        parsers = [
            (PDFParser(), ".pdf"),
            (DOCXParser(), ".docx"),
            (PPTXParser(), ".pptx"),
            (EPUBParser(), ".epub"),
            (RTFParser(), ".rtf"),
        ]

        garbage_bytes = b"\x00\xff\xfe\x01\x02\x03\xde\xad\xbe\xef\xaa\xbb\xcc\xdd" * 10

        for parser, ext in parsers:
            with self.subTest(format=ext):
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp.write(garbage_bytes)
                    tmp_path = Path(tmp.name)

                try:
                    with self.assertRaises(CorruptedDocumentException):
                        parser.parse(tmp_path)
                finally:
                    if tmp_path.exists():
                        tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
