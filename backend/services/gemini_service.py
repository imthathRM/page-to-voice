import os
import logging
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables are loaded
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger("gemini_service")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# Maximum characters per chunk for API requests (keeps within token boundaries and latency limits)
CHUNK_SIZE_CHARS = 4000


def get_genai_client():
    """Initialize and return google-genai Client."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured in backend environment (.env).")
    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


def chunk_text(text: str, max_chars: int = CHUNK_SIZE_CHARS) -> List[str]:
    """Split text into natural paragraph-aligned chunks."""
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para_len = len(para)
        if current_length + para_len > max_chars and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_length = para_len
        else:
            current_chunk.append(para)
            current_length += para_len + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def clean_text_for_narration(text: str, language: str = "en") -> str:
    """
    Use Gemini to clean, polish and prepare text specifically for natural voice narration:
    - Removes visual artifacts, footnotes, citations (e.g. [1], (p. 45)).
    - Expands contractions or symbols (e.g. '&' -> 'and', '%' -> 'percent').
    - Fixes hyphenated line-break words.
    - Preserves language context (English, Tamil, Sinhala).
    """
    if not text or not text.strip():
        return ""

    client = get_genai_client()
    chunks = chunk_text(text, max_chars=3500)
    cleaned_chunks = []

    lang_instruction = {
        "si": "The text is in Sinhala. Clean and format for spoken Sinhala narration without altering meaning or corrupting Unicode script.",
        "ta": "The text is in Tamil. Clean and format for spoken Tamil narration without altering meaning or corrupting Unicode script.",
        "en": "The text is in English. Clean and format for natural English audiobook narration.",
    }.get(language, "Clean and prepare text for natural audiobook narration.")

    prompt_template = (
        f"You are an expert audiobook editor preparing a manuscript for narration. {lang_instruction}\n"
        "Guidelines:\n"
        "1. Remove footnotes, page numbers, bracketed reference numbers like [1], [2], URL links, and non-spoken artifacts.\n"
        "2. Do NOT summarize or shorten the narrative. Keep all actual story/article content intact word-for-word.\n"
        "3. Output ONLY the cleaned narration text with no introductory or meta comments.\n\n"
        "Text to prepare:\n"
    )

    for idx, chunk in enumerate(chunks):
        try:
            response = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=f"{prompt_template}\n{chunk}",
            )
            out_text = response.text.strip() if response.text else chunk
            cleaned_chunks.append(out_text)
        except Exception as exc:
            logger.error(f"Gemini clean text chunk {idx+1} error: {exc}")
            # Fall back to the original chunk if API fails
            cleaned_chunks.append(chunk)

    return "\n\n".join(cleaned_chunks)


def summarize_chapter(text: str, language: str = "en") -> str:
    """
    Generate a concise, insightful chapter summary using Gemini.
    """
    if not text or not text.strip():
        return "No text available for summarization."

    client = get_genai_client()
    # Take up to the first 10,000 chars for summary
    sample_text = text[:10000]

    lang_desc = {"si": "Sinhala", "ta": "Tamil", "en": "English"}.get(language, "English")

    prompt = (
        f"Provide a clear, cohesive 2-3 paragraph summary in {lang_desc} of the following chapter text. "
        "Highlight the key events, arguments, and takeaways. Output ONLY the summary.\n\n"
        f"Chapter Text:\n{sample_text}"
    )

    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
        )
        return response.text.strip() if response.text else "Summary generation returned empty result."
    except Exception as exc:
        logger.error(f"Gemini summarize error: {exc}")
        raise RuntimeError(f"Summarization failed: {str(exc)}")


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate text between English, Tamil, and Sinhala in manageable chunks.
    Preserves paragraph structure and natural reading tone.
    """
    if not text or not text.strip():
        return ""

    if source_lang.lower() == target_lang.lower():
        return text

    client = get_genai_client()
    chunks = chunk_text(text, max_chars=3000)
    translated_chunks = []

    lang_names = {
        "en": "English",
        "si": "Sinhala",
        "ta": "Tamil",
    }
    src_name = lang_names.get(source_lang.lower(), source_lang)
    tgt_name = lang_names.get(target_lang.lower(), target_lang)

    for idx, chunk in enumerate(chunks):
        prompt = (
            f"You are a professional literary translator. Translate the following text from {src_name} to {tgt_name}.\n"
            "Requirements:\n"
            "1. Maintain the emotional tone, style, and literary nuance of the original.\n"
            "2. Preserve paragraph breaks.\n"
            "3. Do not add explanations, notes, or greetings. Output ONLY the translated text.\n\n"
            f"Text:\n{chunk}"
        )
        try:
            response = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt,
            )
            translated_chunks.append(response.text.strip() if response.text else chunk)
        except Exception as exc:
            logger.error(f"Gemini translate chunk {idx+1} error: {exc}")
            raise RuntimeError(f"Translation failed on chunk {idx+1}: {str(exc)}")

    return "\n\n".join(translated_chunks)


def generate_text(prompt: str) -> str:
    """
    General purpose text generation utility for testing.
    """
    client = get_genai_client()
    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
        )
        return response.text.strip() if response.text else ""
    except Exception as exc:
        logger.error(f"Gemini generate text error: {exc}")
        raise RuntimeError(f"Text generation failed: {str(exc)}")

