import re
from typing import List, Dict, Any, Optional
from services.text_processor import clean_text

# Regex patterns for English, Tamil, and Sinhala chapter headings
CHAPTER_PATTERNS = [
    # English
    r"^(?:CHAPTER|Chapter)\s+(?:\d+|[IVXLCDM]+|[A-Za-z]+)(?:\s*[:\-–—]\s*.*)?$",
    r"^(?:Section|SECTION)\s+\d+(?:\s*[:\-–—]\s*.*)?$",
    r"^(?:Part|PART)\s+(?:\d+|[IVXLCDM]+)(?:\s*[:\-–—]\s*.*)?$",
    r"^(?:Act|ACT)\s+(?:\d+|[IVXLCDM]+)(?:\s*[:\-–—]\s*.*)?$",
    # Sinhala: පරිච්ඡේදය (Chapter), කොටස (Part/Section)
    r"^(?:පරිච්ඡේදය|පරිච්ඡෙදය)\s+\d+(?:\s*[:\-–—]\s*.*)?$",
    r"^\d+\s*වන\s*(?:පරිච්ඡේදය|පරිච්ඡෙදය)(?:\s*[:\-–—]\s*.*)?$",
    r"^කොටස\s+\d+(?:\s*[:\-–—]\s*.*)?$",
    # Tamil: அத்தியாயம் (Chapter), பகுதி (Part/Section)
    r"^(?:அத்தியாயம்|அத்தியாயம்:)\s*(?:\d+|[௧-௰]+)(?:\s*[:\-–—]\s*.*)?$",
    r"^(?:\d+|[௧-௰]+)\s*ஆம்\s*அத்தியாயம்(?:\s*[:\-–—]\s*.*)?$",
    r"^பகுதி\s*(?:\d+|[௧-௰]+)(?:\s*[:\-–—]\s*.*)?$",
]

COMBINED_CHAPTER_REGEX = re.compile("|".join(CHAPTER_PATTERNS), re.MULTILINE | re.IGNORECASE)


def detect_chapters(
    raw_text: str,
    headings: Optional[List[Dict[str, Any]]] = None,
    document_title: str = "Document",
) -> List[Dict[str, Any]]:
    """
    Split text into logical chapters based on:
    1. Regular expression matches for Chapter/Section titles (EN, SI, TA).
    2. Document heading structures (e.g. from DOCX/PDF bookmarks).
    3. Fallback: Logical segmentation for large documents without explicit headers.
    
    Returns list of dicts:
    [
        {
            "chapter_number": int,
            "title": str,
            "original_text": str,
            "processed_text": str,
        }
    ]
    """
    if not raw_text or not raw_text.strip():
        return [
            {
                "chapter_number": 1,
                "title": "Full Document",
                "original_text": "",
                "processed_text": "",
            }
        ]

    lines = raw_text.splitlines()
    chapter_splits = []

    # 1. First check explicit heading metadata from DOCX/PDF if available
    heading_titles = set()
    if headings:
        for h in headings:
            t = h.get("title", "").strip()
            if t and len(t) < 100:
                heading_titles.add(t.lower())

    # 2. Scan lines for chapter heading matches
    current_title = "Introduction / Beginning"
    current_lines = []
    chapter_index = 1

    for line_idx, line in enumerate(lines):
        stripped = line.strip()
        is_match = False
        matched_title = ""

        # Check regex
        if COMBINED_CHAPTER_REGEX.match(stripped):
            is_match = True
            matched_title = stripped
        elif stripped.lower() in heading_titles:
            is_match = True
            matched_title = stripped

        if is_match and current_lines:
            text_block = "\n".join(current_lines).strip()
            if len(text_block) > 50:  # Avoid creating tiny empty chapters
                chapter_splits.append({
                    "chapter_number": chapter_index,
                    "title": current_title,
                    "original_text": text_block,
                    "processed_text": clean_text(text_block),
                })
                chapter_index += 1
                current_lines = []
                current_title = matched_title
            else:
                # Append to existing
                current_lines.append(line)
        elif is_match:
            current_title = matched_title
        else:
            current_lines.append(line)

    # Append remaining lines
    if current_lines:
        text_block = "\n".join(current_lines).strip()
        chapter_splits.append({
            "chapter_number": chapter_index,
            "title": current_title if chapter_splits else f"{document_title} - Full Content",
            "original_text": text_block,
            "processed_text": clean_text(text_block),
        })

    # 3. Fallback: If only 1 chapter was found and text is very large (> 15,000 chars),
    # partition into balanced chapters so AI & TTS can process easily
    if len(chapter_splits) == 1 and len(raw_text) > 15000:
        paragraphs = raw_text.split("\n\n")
        chunked_chapters = []
        current_chunk_paras = []
        current_chunk_len = 0
        target_chunk_len = 8000
        p_num = 1

        for p in paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue
            current_chunk_paras.append(p_clean)
            current_chunk_len += len(p_clean)

            if current_chunk_len >= target_chunk_len:
                chunk_text = "\n\n".join(current_chunk_paras)
                chunked_chapters.append({
                    "chapter_number": p_num,
                    "title": f"Chapter {p_num}",
                    "original_text": chunk_text,
                    "processed_text": clean_text(chunk_text),
                })
                p_num += 1
                current_chunk_paras = []
                current_chunk_len = 0

        if current_chunk_paras:
            chunk_text = "\n\n".join(current_chunk_paras)
            chunked_chapters.append({
                "chapter_number": p_num,
                "title": f"Chapter {p_num}",
                "original_text": chunk_text,
                "processed_text": clean_text(chunk_text),
            })

        if len(chunked_chapters) > 1:
            return chunked_chapters

    # Ensure 1-based indexing and formatted titles
    for i, chap in enumerate(chapter_splits):
        chap["chapter_number"] = i + 1
        if not chap["title"]:
            chap["title"] = f"Chapter {i + 1}"

    return chapter_splits

