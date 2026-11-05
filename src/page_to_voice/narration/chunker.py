"""Chunking and narration preparation module for Page to Voice.

Groups sentences into speech-ready chunks with configurable limits, preserving
document headings, chapter metadata, sentence boundaries, and Unicode text.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional

from page_to_voice.cleaning.text_cleaner import clean_text
from page_to_voice.narration.boundary_detector import split_sentences
from page_to_voice.narration.models import Chapter, NarrationChunk, NarrationPlan

logger = logging.getLogger(__name__)

# Default maximum characters per narration chunk (well within TTS API limits)
DEFAULT_MAX_CHARS = 1500

# Estimated average speaking rate in words per second (approx. 150 words per minute)
DEFAULT_WORDS_PER_SECOND = 2.5

# Secondary delimiters for splitting unusually long sentences without cutting words
_CLAUSE_DELIMITERS_REGEX = re.compile(r"([;:\u2014\u2013,]|\s+-\s+)")


def _estimate_duration(word_count: int, character_count: int) -> float:
    """Estimate speech duration in seconds for a given word and character count."""
    if word_count == 0 or character_count == 0:
        return 0.0

    # Primary estimate based on word count (150 wpm = 2.5 words/sec)
    duration = word_count / DEFAULT_WORDS_PER_SECOND

    # Sanity check: In phonetic/syllabic scripts (like Tamil/Sinhala) where word tokenization
    # can differ, ensure at least ~14-16 characters per second
    min_char_duration = character_count / 15.0
    final_duration = max(duration, min_char_duration)
    return round(final_duration, 2)


def _split_long_sentence(sentence: str, max_chars: int) -> List[str]:
    """Split a single sentence that exceeds max_chars at natural clause boundaries or spaces."""
    if len(sentence) <= max_chars:
        return [sentence]

    pieces: List[str] = []
    # Attempt splitting by secondary clause delimiters (;, :, commas, dashes)
    clauses = _CLAUSE_DELIMITERS_REGEX.split(sentence)
    current_clause_buf: List[str] = []
    current_len = 0

    for part in clauses:
        part_len = len(part)
        if current_len + part_len > max_chars and current_clause_buf:
            joined = "".join(current_clause_buf).strip()
            if joined:
                pieces.append(joined)
            current_clause_buf = []
            current_len = 0

        if part_len > max_chars:
            # If an individual clause still exceeds max_chars, split strictly at whitespace
            words = part.split()
            word_buf: List[str] = []
            word_buf_len = 0
            for word in words:
                word_len = len(word) + 1
                if word_buf_len + word_len > max_chars and word_buf:
                    pieces.append(" ".join(word_buf).strip())
                    word_buf = [word]
                    word_buf_len = len(word)
                else:
                    word_buf.append(word)
                    word_buf_len += word_len
            if word_buf:
                current_clause_buf.append(" ".join(word_buf))
                current_len += len(current_clause_buf[-1])
        else:
            current_clause_buf.append(part)
            current_len += part_len

    if current_clause_buf:
        final_piece = "".join(current_clause_buf).strip()
        if final_piece:
            pieces.append(final_piece)

    return pieces or [sentence]


def _build_chunks_from_sentences(
    sentences: List[str],
    max_chars: int,
    start_index: int,
    chapter_title: Optional[str] = None,
    section_title: Optional[str] = None,
) -> List[NarrationChunk]:
    """Group a list of sentences into chunks that do not exceed max_chars."""
    chunks: List[NarrationChunk] = []
    current_sentences: List[str] = []
    current_char_count = 0
    chunk_index = start_index

    # Expand any unusually long individual sentences first
    expanded_sentences: List[str] = []
    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        if len(s_clean) > max_chars:
            expanded_sentences.extend(_split_long_sentence(s_clean, max_chars))
        else:
            expanded_sentences.append(s_clean)

    for sentence in expanded_sentences:
        sentence_len = len(sentence)
        # Adding sentence + a space separator if buffer is not empty
        added_len = sentence_len if current_char_count == 0 else sentence_len + 1

        if current_char_count + added_len > max_chars and current_sentences:
            chunk_text = " ".join(current_sentences).strip()
            words = chunk_text.split()
            w_count = len(words)
            c_count = len(chunk_text)
            chunks.append(
                NarrationChunk(
                    index=chunk_index,
                    text=chunk_text,
                    character_count=c_count,
                    word_count=w_count,
                    estimated_duration_seconds=_estimate_duration(w_count, c_count),
                    chapter_title=chapter_title,
                    section_title=section_title,
                )
            )
            chunk_index += 1
            current_sentences = [sentence]
            current_char_count = sentence_len
        else:
            current_sentences.append(sentence)
            current_char_count += added_len

    if current_sentences:
        chunk_text = " ".join(current_sentences).strip()
        words = chunk_text.split()
        w_count = len(words)
        c_count = len(chunk_text)
        chunks.append(
            NarrationChunk(
                index=chunk_index,
                text=chunk_text,
                character_count=c_count,
                word_count=w_count,
                estimated_duration_seconds=_estimate_duration(w_count, c_count),
                chapter_title=chapter_title,
                section_title=section_title,
            )
        )

    return chunks


def prepare_narration(
    text: Optional[str] = None,
    chapters: Optional[List[Chapter]] = None,
    max_chars: int = DEFAULT_MAX_CHARS,
    auto_clean: bool = True,
) -> NarrationPlan:
    """Prepare cleaned text or structured chapters into a speech-ready NarrationPlan.

    Args:
        text: Raw or cleaned document text string. Optional if chapters are provided.
        chapters: Optional list of structured Chapter objects.
        max_chars: Maximum character limit for each narration chunk (default 1500).
        auto_clean: Whether to apply clean_text to input text before chunking.

    Returns:
        NarrationPlan containing ordered chunks and comprehensive statistics.

    Raises:
        ValueError: If max_chars is non-positive, or if neither text nor chapters are provided.
    """
    if max_chars <= 0:
        raise ValueError(f"max_chars must be a positive integer, got {max_chars}.")

    if text is None and not chapters:
        logger.debug("prepare_narration called with no text and no chapters.")
        return NarrationPlan(
            total_chunks=0,
            total_characters=0,
            total_words=0,
            estimated_total_duration_seconds=0.0,
            chunks=[],
        )

    all_chunks: List[NarrationChunk] = []

    if chapters:
        # Process each chapter sequentially
        current_chunk_idx = 0
        for chapter in chapters:
            c_text = clean_text(chapter.content) if auto_clean else chapter.content
            sentences = split_sentences(c_text)
            chapter_chunks = _build_chunks_from_sentences(
                sentences=sentences,
                max_chars=max_chars,
                start_index=current_chunk_idx,
                chapter_title=chapter.title,
                section_title=chapter.section_title,
            )
            all_chunks.extend(chapter_chunks)
            current_chunk_idx += len(chapter_chunks)
    elif text is not None:
        c_text = clean_text(text) if auto_clean else text
        sentences = split_sentences(c_text)
        all_chunks = _build_chunks_from_sentences(
            sentences=sentences,
            max_chars=max_chars,
            start_index=0,
        )

    total_chars = sum(c.character_count for c in all_chunks)
    total_words = sum(c.word_count for c in all_chunks)
    total_duration = round(sum(c.estimated_duration_seconds for c in all_chunks), 2)

    logger.info(
        "Prepared narration plan: %d chunks, %d words, %d chars, ~%.2fs estimated duration.",
        len(all_chunks),
        total_words,
        total_chars,
        total_duration,
    )

    return NarrationPlan(
        total_chunks=len(all_chunks),
        total_characters=total_chars,
        total_words=total_words,
        estimated_total_duration_seconds=total_duration,
        chunks=all_chunks,
    )
