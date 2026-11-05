"""
Corpus Generator for Page to Voice Document Processing Test Suite.

Generates actual test documents across all six formats (PDF, DOCX, TXT,
PPTX, EPUB, RTF) containing known English, Tamil, and Sinhala text,
as well as deliberately corrupted malformed fixtures for error testing.
"""

from __future__ import annotations

import binascii
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

# Determine paths relative to this script
FIXTURES_DIR = Path(__file__).resolve().parent
DOCS_DIR = FIXTURES_DIR / "documents"
MALFORMED_DIR = FIXTURES_DIR / "malformed"
EXPECTED_DIR = FIXTURES_DIR / "expected"

# Ensure directories exist
DOCS_DIR.mkdir(parents=True, exist_ok=True)
MALFORMED_DIR.mkdir(parents=True, exist_ok=True)
EXPECTED_DIR.mkdir(parents=True, exist_ok=True)

# Canonical multilingual text corpus
EXPECTED_DATA = {
    "title": "Page to Voice Multi-Language Test Document",
    "section1": {
        "heading": "Page to Voice Multi-Language Test Document",
        "english": (
            "Page to Voice is an intelligent audiobook generation and listening platform "
            "designed to convert written documents into accessible, high-quality audio."
        ),
        "tamil": (
            "பக்கம் முதல் குரல் வரை: அறிவார்ந்த ஒலிப்புத்தகம் உருவாக்கும் தளம். "
            "இது எழுத்துப்பூர்வ ஆவணங்களை உயர்தர ஆடியோவாக மாற்றுகிறது."
        ),
        "sinhala": (
            "පිටුවෙන් හඬට: බුද්ධිමත් ශ්‍රව්‍ය පොත් නිර්මාණ වේදිකාව. "
            "මෙමඟින් ලියැවුණු ලේඛන උසස් තත්ත්වයේ හඬ බවට පරිවර්තනය කරයි."
        ),
    },
    "section2": {
        "heading": "Advanced Linguistic and Technical Evaluation",
        "special_characters": (
            "Special characters test: Quotes “Double” and ‘Single’. Symbols: ©, ®, ™, §, €, £, ¥, →, ★. "
            "Math: α + β = γ. Punctuation: — (em-dash), … (ellipsis), ¿¡."
        ),
        "tamil_complex": (
            "தமிழ் மொழி உலகின் மிகத் தொன்மையான செம்மொழிகளில் ஒன்றாகும். "
            "தொழில்நுட்ப சோதனையில் அனைத்து எழுத்துக்களும் சரியாகப் பாதுகாக்கப்பட வேண்டும்."
        ),
        "sinhala_complex": (
            "සිංහල භාෂාව ඉන්දු-ආර්ය භාෂා පවුලට අයත් වන අතර දිවයිනේ ප්‍රධාන භාෂාවකි. "
            "තාක්ෂණික පරීක්ෂණයේදී සියලුම අක්ෂර නිවැරදිව කියවිය යුතුය."
        ),
    },
}


def generate_expected_json() -> None:
    """Save canonical reference text to expected_text.json."""
    json_path = EXPECTED_DIR / "expected_text.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(EXPECTED_DATA, f, ensure_ascii=False, indent=2)
    print(f"Generated {json_path}")


def generate_txt() -> None:
    """Generate sample.txt."""
    s1 = EXPECTED_DATA["section1"]
    s2 = EXPECTED_DATA["section2"]

    content = (
        f"{s1['heading']}\n\n"
        f"{s1['english']}\n\n"
        f"{s1['tamil']}\n\n"
        f"{s1['sinhala']}\n\n"
        f"{s2['heading']}\n\n"
        f"{s2['special_characters']}\n\n"
        f"{s2['tamil_complex']}\n\n"
        f"{s2['sinhala_complex']}\n"
    )

    path = DOCS_DIR / "sample.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated {path}")


def generate_docx() -> None:
    """Generate sample.docx with OpenXML structure."""
    path = DOCS_DIR / "sample.docx"
    s1 = EXPECTED_DATA["section1"]
    s2 = EXPECTED_DATA["section2"]

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        '  <Default Extension="xml" ContentType="application/xml"/>\n'
        '  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\n'
        '</Types>'
    )

    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>\n'
        '</Relationships>'
    )

    def xml_p(text: str, is_heading: bool = False, heading_level: int = 1) -> str:
        escaped = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        style = (
            f'<w:pPr><w:pStyle w:val="Heading{heading_level}"/></w:pPr>'
            if is_heading
            else ""
        )
        return f"<w:p>{style}<w:r><w:t>{escaped}</w:t></w:r></w:p>"

    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
        "  <w:body>\n"
        f"    {xml_p(s1['heading'], is_heading=True, heading_level=1)}\n"
        f"    {xml_p(s1['english'])}\n"
        f"    {xml_p(s1['tamil'])}\n"
        f"    {xml_p(s1['sinhala'])}\n"
        f"    {xml_p(s2['heading'], is_heading=True, heading_level=2)}\n"
        f"    {xml_p(s2['special_characters'])}\n"
        f"    {xml_p(s2['tamil_complex'])}\n"
        f"    {xml_p(s2['sinhala_complex'])}\n"
        "  </w:body>\n"
        "</w:document>"
    )

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", doc_xml.encode("utf-8"))
    print(f"Generated {path}")


def generate_pptx() -> None:
    """Generate sample.pptx containing 2 slides."""
    path = DOCS_DIR / "sample.pptx"
    s1 = EXPECTED_DATA["section1"]
    s2 = EXPECTED_DATA["section2"]

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        '  <Default Extension="xml" ContentType="application/xml"/>\n'
        '  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>\n'
        '  <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>\n'
        '  <Override PartName="/ppt/slides/slide2.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>\n'
        '</Types>'
    )

    pkg_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>\n'
        '</Relationships>'
    )

    pres_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">\n'
        '  <p:sldIdLst>\n'
        '    <p:sldId id="256" r:id="rId1"/>\n'
        '    <p:sldId id="257" r:id="rId2"/>\n'
        '  </p:sldIdLst>\n'
        '</p:presentation>'
    )

    pres_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>\n'
        '  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide2.xml"/>\n'
        '</Relationships>'
    )

    def escape_xml(t: str) -> str:
        return (
            t.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def make_slide_xml(title: str, paragraphs: list[str]) -> str:
        shapes = []
        # Title shape
        shapes.append(
            '<p:sp>\n'
            '  <p:txBody>\n'
            '    <a:bodyPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>\n'
            f'    <a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:r><a:t>{escape_xml(title)}</a:t></a:r></a:p>\n'
            '  </p:txBody>\n'
            '</p:sp>'
        )
        # Content shape
        p_elements = "".join(
            f'<a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:r><a:t>{escape_xml(p)}</a:t></a:r></a:p>\n'
            for p in paragraphs
        )
        shapes.append(
            '<p:sp>\n'
            '  <p:txBody>\n'
            '    <a:bodyPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>\n'
            f'    {p_elements}\n'
            '  </p:txBody>\n'
            '</p:sp>'
        )

        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">\n'
            '  <p:cSld>\n'
            '    <p:spTree>\n'
            f'      {"".join(shapes)}\n'
            '    </p:spTree>\n'
            '  </p:cSld>\n'
            '</p:sld>'
        )

    slide1_xml = make_slide_xml(s1["heading"], [s1["english"], s1["tamil"], s1["sinhala"]])
    slide2_xml = make_slide_xml(s2["heading"], [s2["special_characters"], s2["tamil_complex"], s2["sinhala_complex"]])

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", pkg_rels)
        zf.writestr("ppt/presentation.xml", pres_xml)
        zf.writestr("ppt/_rels/presentation.xml.rels", pres_rels)
        zf.writestr("ppt/slides/slide1.xml", slide1_xml.encode("utf-8"))
        zf.writestr("ppt/slides/slide2.xml", slide2_xml.encode("utf-8"))
    print(f"Generated {path}")


def generate_epub() -> None:
    """Generate sample.epub with 2 chapters."""
    path = DOCS_DIR / "sample.epub"
    s1 = EXPECTED_DATA["section1"]
    s2 = EXPECTED_DATA["section2"]

    container_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '  <rootfiles>\n'
        '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
        '  </rootfiles>\n'
        '</container>'
    )

    content_opf = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookID" version="2.0">\n'
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        '    <dc:title>Page to Voice Multi-Language Test Document</dc:title>\n'
        '    <dc:language>en</dc:language>\n'
        '    <dc:identifier id="BookID">urn:uuid:12345678-1234-5678-1234-567812345678</dc:identifier>\n'
        '  </metadata>\n'
        '  <manifest>\n'
        '    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>\n'
        '    <item id="chap1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>\n'
        '    <item id="chap2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>\n'
        '  </manifest>\n'
        '  <spine toc="ncx">\n'
        '    <itemref idref="chap1"/>\n'
        '    <itemref idref="chap2"/>\n'
        '  </spine>\n'
        '</package>'
    )

    toc_ncx = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
        '  <head><meta name="dtb:uid" content="urn:uuid:12345678-1234-5678-1234-567812345678"/></head>\n'
        '  <docTitle><text>Page to Voice Multi-Language Test Document</text></docTitle>\n'
        '  <navMap>\n'
        '    <navPoint id="np-1" playOrder="1"><navLabel><text>Chapter 1</text></navLabel><content src="chapter1.xhtml"/></navPoint>\n'
        '    <navPoint id="np-2" playOrder="2"><navLabel><text>Chapter 2</text></navLabel><content src="chapter2.xhtml"/></navPoint>\n'
        '  </navMap>\n'
        '</ncx>'
    )

    def escape_html(t: str) -> str:
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    chap1_html = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
        '<html xmlns="http://www.w3.org/1999/xhtml">\n'
        '<head><title>Chapter 1 - Overview</title></head>\n'
        '<body>\n'
        f'  <h1>{escape_html(s1["heading"])}</h1>\n'
        f'  <p>{escape_html(s1["english"])}</p>\n'
        f'  <p>{escape_html(s1["tamil"])}</p>\n'
        f'  <p>{escape_html(s1["sinhala"])}</p>\n'
        '</body>\n'
        '</html>'
    )

    chap2_html = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
        '<html xmlns="http://www.w3.org/1999/xhtml">\n'
        '<head><title>Chapter 2 - Evaluation</title></head>\n'
        '<body>\n'
        f'  <h2>{escape_html(s2["heading"])}</h2>\n'
        f'  <p>{escape_html(s2["special_characters"])}</p>\n'
        f'  <p>{escape_html(s2["tamil_complex"])}</p>\n'
        f'  <p>{escape_html(s2["sinhala_complex"])}</p>\n'
        '</body>\n'
        '</html>'
    )

    with zipfile.ZipFile(path, "w") as zf:
        # mimetype must be first, uncompressed
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/content.opf", content_opf, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/toc.ncx", toc_ncx, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/chapter1.xhtml", chap1_html.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/chapter2.xhtml", chap2_html.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)
    print(f"Generated {path}")


def generate_rtf() -> None:
    """Generate sample.rtf with Unicode escape codes."""
    path = DOCS_DIR / "sample.rtf"
    s1 = EXPECTED_DATA["section1"]
    s2 = EXPECTED_DATA["section2"]

    def to_rtf(text: str) -> str:
        parts = []
        for ch in text:
            cp = ord(ch)
            if cp < 128 and ch not in ("{", "}", "\\"):
                parts.append(ch)
            elif ch in ("{", "}", "\\"):
                parts.append("\\" + ch)
            else:
                signed = cp if cp < 32768 else cp - 65536
                parts.append(f"\\u{signed}?")
        return "".join(parts)

    rtf_content = (
        "{\\rtf1\\ansi\\ansicpg1252\\deff0\\nouicompat\\deflang1033\n"
        "{\\fonttbl{\\f0\\fnil\\fcharset0 Arial;}{\\f1\\fnil\\fcharset0 Nirmala UI;}}\n"
        "\\viewkind4\\uc1\n"
        f"\\pard\\f0\\b\\fs28 {to_rtf(s1['heading'])}\\b0\\fs22\\par\\par\n"
        f"{to_rtf(s1['english'])}\\par\\par\n"
        f"\\f1 {to_rtf(s1['tamil'])}\\par\\par\n"
        f"{to_rtf(s1['sinhala'])}\\f0\\par\\par\n"
        f"\\b\\fs26 {to_rtf(s2['heading'])}\\b0\\fs22\\par\\par\n"
        f"{to_rtf(s2['special_characters'])}\\par\\par\n"
        f"\\f1 {to_rtf(s2['tamil_complex'])}\\par\\par\n"
        f"{to_rtf(s2['sinhala_complex'])}\\f0\\par\n"
        "}"
    )

    with open(path, "w", encoding="ascii") as f:
        f.write(rtf_content)
    print(f"Generated {path}")


def generate_pdf() -> None:
    """Generate sample.pdf with 2 pages and UTF-16BE text streams."""
    path = DOCS_DIR / "sample.pdf"
    s1 = EXPECTED_DATA["section1"]
    s2 = EXPECTED_DATA["section2"]

    def to_hex(s: str) -> str:
        raw = s.encode("utf-16-be")
        return "<feff" + binascii.hexlify(raw).decode("ascii") + ">"

    # Stream 1: Page 1 content
    stream1_text = (
        f"BT /F1 16 Tf 50 750 Td {to_hex(s1['heading'])} Tj ET\n"
        f"BT /F1 11 Tf 50 700 Td {to_hex(s1['english'])} Tj ET\n"
        f"BT /F1 11 Tf 50 630 Td {to_hex(s1['tamil'])} Tj ET\n"
        f"BT /F1 11 Tf 50 560 Td {to_hex(s1['sinhala'])} Tj ET\n"
    )
    stream1 = stream1_text.encode("latin-1")

    # Stream 2: Page 2 content
    stream2_text = (
        f"BT /F1 16 Tf 50 750 Td {to_hex(s2['heading'])} Tj ET\n"
        f"BT /F1 11 Tf 50 700 Td {to_hex(s2['special_characters'])} Tj ET\n"
        f"BT /F1 11 Tf 50 630 Td {to_hex(s2['tamil_complex'])} Tj ET\n"
        f"BT /F1 11 Tf 50 560 Td {to_hex(s2['sinhala_complex'])} Tj ET\n"
    )
    stream2 = stream2_text.encode("latin-1")

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n")

    # Object 1: Catalog
    o1 = len(pdf)
    pdf.extend(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    # Object 2: Pages root
    o2 = len(pdf)
    pdf.extend(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>\nendobj\n")

    # Object 3: Page 1
    o3 = len(pdf)
    pdf.extend(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R >>\nendobj\n")

    # Object 4: Page 2
    o4 = len(pdf)
    pdf.extend(b"4 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 6 0 R >>\nendobj\n")

    # Object 5: Content Stream Page 1
    o5 = len(pdf)
    pdf.extend(f"5 0 obj\n<< /Length {len(stream1)} >>\nstream\n".encode("ascii"))
    pdf.extend(stream1)
    pdf.extend(b"\nendstream\nendobj\n")

    # Object 6: Content Stream Page 2
    o6 = len(pdf)
    pdf.extend(f"6 0 obj\n<< /Length {len(stream2)} >>\nstream\n".encode("ascii"))
    pdf.extend(stream2)
    pdf.extend(b"\nendstream\nendobj\n")

    # Xref Table
    xref_offset = len(pdf)
    pdf.extend(b"xref\n0 7\n0000000000 65535 f \n")
    for off in (o1, o2, o3, o4, o5, o6):
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    # Trailer
    pdf.extend(
        f"trailer\n<< /Size 7 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )

    with open(path, "wb") as f:
        f.write(pdf)
    print(f"Generated {path}")


def generate_malformed() -> None:
    """Generate corrupt/malformed test fixtures for all five binary/formatted types."""
    # invalid.pdf: Corrupted header, truncated PDF data
    p_pdf = MALFORMED_DIR / "invalid.pdf"
    with open(p_pdf, "wb") as f:
        f.write(b"%PDF-1.4\n1 0 obj<< /CorruptData null >>\ntruncated-stream-without-xref-or-trailer")
    print(f"Generated {p_pdf}")

    # invalid.docx: Truncated ZIP header
    p_docx = MALFORMED_DIR / "invalid.docx"
    with open(p_docx, "wb") as f:
        f.write(b"PK\x03\x04\x14\x00\x00\x00\x08\x00corrupted-docx-archive-bytes-truncated")
    print(f"Generated {p_docx}")

    # invalid.pptx: Invalid ZIP file
    p_pptx = MALFORMED_DIR / "invalid.pptx"
    with open(p_pptx, "wb") as f:
        f.write(b"PK\x03\x04\x00\x00bad-pptx-header-data")
    print(f"Generated {p_pptx}")

    # invalid.epub: Missing container and invalid package
    p_epub = MALFORMED_DIR / "invalid.epub"
    with open(p_epub, "wb") as f:
        f.write(b"Not An EPUB File Content At All")
    print(f"Generated {p_epub}")

    # invalid.rtf: Not starting with {\rtf and malformed braces
    p_rtf = MALFORMED_DIR / "invalid.rtf"
    with open(p_rtf, "wb") as f:
        f.write(b"This is not a valid RTF document. {Unbalanced braces \\u999999")
    print(f"Generated {p_rtf}")


def main() -> None:
    print("Generating Page to Voice test fixtures...")
    generate_expected_json()
    generate_txt()
    generate_docx()
    generate_pptx()
    generate_epub()
    generate_rtf()
    generate_pdf()
    generate_malformed()
    print("All fixtures generated successfully!")


if __name__ == "__main__":
    main()
