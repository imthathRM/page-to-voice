"""
Automated Tests for Document Parsers and Common Parser Interface.

Verifies:
- All six document parsers follow the common interface.
- Format identification and support detection.
- Rejection of unsupported formats and non-existent files.
- Text extraction fidelity across PDF, DOCX, TXT, PPTX, EPUB, RTF.
- Preservation of structural boundaries (pages, slides, chapters, paragraphs).
- Graceful handling of empty documents.
- In-memory bytes parsing and serialization.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import unittest

# Ensure backend is in path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from document_processing import (
    BaseDocumentParser,
    CorruptedDocumentException,
    DOCXParser,
    DocumentParserFactory,
    DocumentSection,
    EPUBParser,
    ExtractionResult,
    ExtractionStatus,
    FileAccessError,
    PDFParser,
    PPTXParser,
    RTFParser,
    TXTParser,
    UnsupportedFileFormatException,
    get_default_factory,
    get_parser_for_file,
    get_supported_formats,
    parse_document,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
DOCS_DIR = FIXTURES_DIR / "documents"
EXPECTED_DIR = FIXTURES_DIR / "expected"


class TestParserInterfaceAndExtraction(unittest.TestCase):
    """Test suite for Common Parser Interface and individual parsers."""

    @classmethod
    def setUpClass(cls) -> None:
        expected_json_path = EXPECTED_DIR / "expected_text.json"
        with open(expected_json_path, "r", encoding="utf-8") as f:
            cls.expected_data = json.load(f)

    def test_all_parsers_follow_common_interface(self) -> None:
        """Verify that all six parsers inherit from BaseDocumentParser and define required attributes."""
        parsers = [
            PDFParser(),
            DOCXParser(),
            TXTParser(),
            PPTXParser(),
            EPUBParser(),
            RTFParser(),
        ]

        for p in parsers:
            with self.subTest(parser=p.parser_name):
                self.assertIsInstance(p, BaseDocumentParser)
                self.assertTrue(len(p.supported_formats) > 0)
                self.assertIsInstance(p.parser_name, str)
                self.assertTrue(callable(getattr(p, "supports", None)))
                self.assertTrue(callable(getattr(p, "validate_file", None)))
                self.assertTrue(callable(getattr(p, "parse", None)))
                self.assertTrue(callable(getattr(p, "parse_bytes", None)))

    def test_supported_formats_and_extension_matching(self) -> None:
        """Verify that each parser correctly identifies supported and unsupported extensions."""
        cases = [
            (PDFParser(), "document.pdf", True),
            (PDFParser(), "doc.PDF", True),
            (PDFParser(), "document.docx", False),
            (DOCXParser(), "document.docx", True),
            (DOCXParser(), "document.txt", False),
            (TXTParser(), "notes.txt", True),
            (TXTParser(), "presentation.pptx", False),
            (PPTXParser(), "slides.pptx", True),
            (PPTXParser(), "book.epub", False),
            (EPUBParser(), "novel.epub", True),
            (EPUBParser(), "doc.rtf", False),
            (RTFParser(), "letter.rtf", True),
            (RTFParser(), "doc.pdf", False),
        ]

        for parser, filename, expected in cases:
            with self.subTest(parser=parser.parser_name, file=filename):
                self.assertEqual(parser.supports(filename), expected)

    def test_factory_registry_and_discovery(self) -> None:
        """Verify DocumentParserFactory registers all six formats and retrieves correct parsers."""
        factory = get_default_factory()
        formats = factory.get_supported_formats()

        for expected_fmt in ["pdf", "docx", "txt", "pptx", "epub", "rtf"]:
            self.assertIn(expected_fmt, formats)

        self.assertIsInstance(factory.get_parser("file.pdf"), PDFParser)
        self.assertIsInstance(factory.get_parser("file.docx"), DOCXParser)
        self.assertIsInstance(factory.get_parser("file.txt"), TXTParser)
        self.assertIsInstance(factory.get_parser("file.pptx"), PPTXParser)
        self.assertIsInstance(factory.get_parser("file.epub"), EPUBParser)
        self.assertIsInstance(factory.get_parser("file.rtf"), RTFParser)

    def test_unsupported_format_raises_exception(self) -> None:
        """Verify that unsupported extensions safely raise UnsupportedFileFormatException."""
        unsupported_files = ["audio.mp3", "video.mp4", "archive.zip", "unknown.xyz"]
        for uf in unsupported_files:
            with self.subTest(file=uf):
                with self.assertRaises(UnsupportedFileFormatException):
                    get_parser_for_file(uf)

    def test_nonexistent_file_raises_file_access_error(self) -> None:
        """Verify that attempting to parse a non-existent file raises FileAccessError."""
        fake_path = DOCS_DIR / "non_existent_document_12345.pdf"
        parser = PDFParser()
        with self.assertRaises(FileAccessError):
            parser.parse(fake_path)

    def test_txt_parser_extraction(self) -> None:
        """Verify text extraction from sample.txt."""
        path = DOCS_DIR / "sample.txt"
        res = parse_document(path)

        self.assertEqual(res.status, ExtractionStatus.SUCCESS)
        self.assertEqual(res.file_type, "txt")
        self.assertIn(self.expected_data["title"], res.text)
        self.assertIn("Page to Voice is an intelligent audiobook", res.text)
        self.assertTrue(len(res.sections) >= 5)

    def test_docx_parser_extraction(self) -> None:
        """Verify text extraction from sample.docx."""
        path = DOCS_DIR / "sample.docx"
        res = parse_document(path)

        self.assertEqual(res.status, ExtractionStatus.SUCCESS)
        self.assertEqual(res.file_type, "docx")
        self.assertIn(self.expected_data["title"], res.text)
        self.assertIn("Page to Voice is an intelligent audiobook", res.text)
        self.assertTrue(len(res.sections) >= 5)

    def test_pptx_parser_extraction_and_slide_boundaries(self) -> None:
        """Verify slide-by-slide text extraction from sample.pptx."""
        path = DOCS_DIR / "sample.pptx"
        res = parse_document(path)

        self.assertEqual(res.status, ExtractionStatus.SUCCESS)
        self.assertEqual(res.file_type, "pptx")
        self.assertEqual(len(res.sections), 2)  # 2 slides
        self.assertEqual(res.sections[0].section_type, "slide")
        self.assertEqual(res.sections[1].section_type, "slide")
        self.assertIn(self.expected_data["title"], res.sections[0].content)
        self.assertIn("Advanced Linguistic", res.sections[1].content)

    def test_epub_parser_extraction_and_chapters(self) -> None:
        """Verify chapter-by-chapter extraction from sample.epub."""
        path = DOCS_DIR / "sample.epub"
        res = parse_document(path)

        self.assertEqual(res.status, ExtractionStatus.SUCCESS)
        self.assertEqual(res.file_type, "epub")
        self.assertEqual(len(res.sections), 2)  # 2 chapters
        self.assertEqual(res.sections[0].section_type, "chapter")
        self.assertEqual(res.sections[1].section_type, "chapter")
        self.assertIn("Page to Voice", res.sections[0].content)
        self.assertIn("Advanced Linguistic", res.sections[1].content)

    def test_rtf_parser_extraction(self) -> None:
        """Verify text extraction from sample.rtf."""
        path = DOCS_DIR / "sample.rtf"
        res = parse_document(path)

        self.assertEqual(res.status, ExtractionStatus.SUCCESS)
        self.assertEqual(res.file_type, "rtf")
        self.assertIn("Page to Voice Multi-Language Test Document", res.text)
        self.assertIn("Page to Voice is an intelligent audiobook", res.text)
        self.assertTrue(len(res.sections) >= 5)

    def test_pdf_parser_extraction_and_page_boundaries(self) -> None:
        """Verify page-by-page text extraction from sample.pdf."""
        path = DOCS_DIR / "sample.pdf"
        res = parse_document(path)

        self.assertEqual(res.status, ExtractionStatus.SUCCESS)
        self.assertEqual(res.file_type, "pdf")
        self.assertEqual(len(res.sections), 2)  # 2 pages
        self.assertEqual(res.sections[0].section_type, "page")
        self.assertEqual(res.sections[1].section_type, "page")
        self.assertIn(self.expected_data["title"], res.sections[0].content)
        self.assertIn("Advanced Linguistic", res.sections[1].content)

    def test_empty_text_document(self) -> None:
        """Verify that an empty text file is parsed without crashing."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            tname = f.name

        try:
            res = parse_document(tname)
            self.assertEqual(res.status, ExtractionStatus.SUCCESS)
            self.assertEqual(res.text, "")
            self.assertTrue(len(res.warnings) > 0)
        finally:
            if os.path.exists(tname):
                os.unlink(tname)

    def test_parse_bytes_in_memory(self) -> None:
        """Verify parsing directly from in-memory byte buffer."""
        parser = TXTParser()
        content = "Paragraph 1\n\nParagraph 2 with Tamil: தமிழ்".encode("utf-8")
        res = parser.parse_bytes(content, file_name="in_memory.txt")

        self.assertEqual(res.status, ExtractionStatus.SUCCESS)
        self.assertEqual(res.file_name, "in_memory.txt")
        self.assertIn("Paragraph 1", res.text)
        self.assertIn("தமிழ்", res.text)
        self.assertEqual(len(res.sections), 2)

    def test_extraction_result_serialization(self) -> None:
        """Verify ExtractionResult.to_dict() returns a valid JSON-serializable dictionary."""
        path = DOCS_DIR / "sample.txt"
        res = parse_document(path)
        d = res.to_dict()

        self.assertIsInstance(d, dict)
        self.assertIn("text", d)
        self.assertIn("file_name", d)
        self.assertIn("file_type", d)
        self.assertIn("status", d)
        self.assertIn("sections", d)
        self.assertIn("warnings", d)
        self.assertIn("metadata", d)
        # Verify JSON dump works without error
        json_str = json.dumps(d)
        self.assertTrue(len(json_str) > 0)


if __name__ == "__main__":
    unittest.main()
