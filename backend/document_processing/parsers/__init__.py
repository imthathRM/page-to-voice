"""
Format-specific document parsers for Page to Voice.
"""

from .docx_parser import DOCXParser
from .epub_parser import EPUBParser
from .pdf_parser import PDFParser
from .pptx_parser import PPTXParser
from .rtf_parser import RTFParser
from .txt_parser import TXTParser

__all__ = [
    "PDFParser",
    "DOCXParser",
    "TXTParser",
    "PPTXParser",
    "EPUBParser",
    "RTFParser",
]
