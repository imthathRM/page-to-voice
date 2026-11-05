import io
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import fitz  # PyMuPDF
import docx  # python-docx
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

logger = logging.getLogger("document_parser")


class ParsedDocument:
    def __init__(
        self,
        full_text: str,
        page_count: int = 1,
        headings: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        pages_text: Optional[List[str]] = None,
    ):
        self.full_text = full_text
        self.page_count = page_count
        self.headings = headings or []
        self.metadata = metadata or {}
        self.pages_text = pages_text or []


def extract_text_from_pdf(filepath: str) -> ParsedDocument:
    """
    Extract text from PDF pages using PyMuPDF (fitz).
    Preserves page order, detects empty or image-only pages, and triggers OCR when appropriate.
    Does NOT invoke OCR unnecessarily if extractable text is present.
    """
    doc = fitz.open(filepath)
    pages_text = []
    headings = []
    scanned_pages_count = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()

        # If page has little or no text, check if it contains images (scanned page)
        if len(text) < 30:
            image_list = page.get_images(full=True)
            if image_list and pytesseract:
                # Attempt OCR on the largest image in the page
                try:
                    ocr_page_text = ""
                    for img_index, img_info in enumerate(image_list[:2]):
                        xref = img_info[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        pil_img = Image.open(io.BytesIO(image_bytes))

                        # Run pytesseract OCR
                        recognized = pytesseract.image_to_string(pil_img)
                        if recognized.strip():
                            ocr_page_text += "\n" + recognized.strip()

                    if ocr_page_text.strip():
                        text = ocr_page_text.strip()
                        scanned_pages_count += 1
                except Exception as ocr_err:
                    logger.warning(f"OCR fallback failed on PDF page {page_num + 1}: {ocr_err}")

        # Extract table of contents / bookmarks if on first page
        if page_num == 0:
            toc = doc.get_toc()
            if toc:
                for item in toc:
                    # toc item format: [lvl, title, page, ...]
                    if len(item) >= 2:
                        headings.append({"level": item[0], "title": item[1], "page": item[2] if len(item) > 2 else 1})

        pages_text.append(text)

    full_text = "\n\n".join(pages_text)
    metadata = {
        "format": "PDF",
        "page_count": len(doc),
        "scanned_pages_detected": scanned_pages_count,
        "author": doc.metadata.get("author") if doc.metadata else None,
        "title": doc.metadata.get("title") if doc.metadata else None,
    }
    doc.close()
    return ParsedDocument(full_text=full_text, page_count=len(pages_text), headings=headings, metadata=metadata, pages_text=pages_text)


def extract_text_from_docx(filepath: str) -> ParsedDocument:
    """
    Extract text and heading structure from a DOCX file using python-docx.
    Preserves reading order and hierarchical heading information.
    """
    document = docx.Document(filepath)
    paragraphs_text = []
    headings = []

    for idx, p in enumerate(document.paragraphs):
        p_text = p.text.strip()
        if not p_text:
            continue

        style_name = p.style.name.lower() if p.style else ""
        if "heading" in style_name:
            level = 1
            if style_name.startswith("heading 1"):
                level = 1
            elif style_name.startswith("heading 2"):
                level = 2
            elif style_name.startswith("heading 3"):
                level = 3
            headings.append({"level": level, "title": p_text, "paragraph_index": idx})

        paragraphs_text.append(p_text)

    full_text = "\n\n".join(paragraphs_text)
    metadata = {
        "format": "DOCX",
        "paragraph_count": len(paragraphs_text),
        "heading_count": len(headings),
    }
    return ParsedDocument(full_text=full_text, page_count=max(1, len(paragraphs_text) // 25), headings=headings, metadata=metadata)


def extract_text_from_txt(filepath: str) -> ParsedDocument:
    """
    Extract text from a plain TXT file using built-in file handling.
    Safely handles UTF-8, UTF-8-BOM, and fallback encodings (latin-1).
    Preserves meaningful paragraph structure.
    """
    content = ""
    encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

    for enc in encodings_to_try:
        try:
            with open(filepath, "r", encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, Exception):
            continue

    if not content:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

    lines = content.splitlines()
    paragraphs = []
    current_para = []

    for line in lines:
        stripped = line.strip()
        if stripped:
            current_para.append(stripped)
        elif current_para:
            paragraphs.append(" ".join(current_para))
            current_para = []

    if current_para:
        paragraphs.append(" ".join(current_para))

    full_text = "\n\n".join(paragraphs) if paragraphs else content
    metadata = {
        "format": "TXT",
        "line_count": len(lines),
        "paragraph_count": len(paragraphs),
    }
    return ParsedDocument(full_text=full_text, page_count=max(1, len(paragraphs) // 25), metadata=metadata)


def extract_document_text(filepath: str) -> ParsedDocument:
    """
    Master extraction router based on file extension.
    Supports .pdf, .docx, and .txt.
    """
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(filepath)
    elif ext == ".docx":
        return extract_text_from_docx(filepath)
    elif ext == ".txt":
        return extract_text_from_txt(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

