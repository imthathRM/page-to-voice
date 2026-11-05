import os
import time
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Generator, List
from dotenv import load_dotenv
import httpx

# Ensure environment variables are loaded
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger("elevenlabs_service")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_DEFAULT_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5").strip()

# Curated ElevenLabs voices suitable for audiobook narration
AVAILABLE_ELEVENLABS_VOICES: List[Dict[str, str]] = [
    {"name": "21m00Tcm4TlvDq8ikWAM", "label": "Rachel (Calm Narration)", "gender": "Female", "locale": "en-US"},
    {"name": "pNInz6obpgDQGcFmaJgB", "label": "Adam (Deep Narrator)", "gender": "Male", "locale": "en-US"},
    {"name": "AZnzlk1XvdvUeBnXmlld", "label": "Domi (Clear Audiobook)", "gender": "Female", "locale": "en-US"},
    {"name": "TxGEqnHWrfWFTfGW9XjX", "label": "Josh (Warm Storyteller)", "gender": "Male", "locale": "en-US"},
]

DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel


def is_elevenlabs_configured() -> bool:
    """Return True if ElevenLabs API key is configured."""
    key = os.getenv("ELEVENLABS_API_KEY", ELEVENLABS_API_KEY).strip()
    return bool(key)


def get_available_voices() -> List[Dict[str, str]]:
    """Return catalog of optimized ElevenLabs Flash voices."""
    return AVAILABLE_ELEVENLABS_VOICES


def stream_elevenlabs_audio(
    text: str,
    voice_id: Optional[str] = None,
    model_id: Optional[str] = None,
) -> Generator[bytes, None, None]:
    """
    Stream MP3 audio chunks in real-time from ElevenLabs Flash v2.5 API.
    Ultra-low latency (~75ms-150ms TTFB).
    """
    key = os.getenv("ELEVENLABS_API_KEY", ELEVENLABS_API_KEY).strip()
    if not key:
        raise ValueError("ELEVENLABS_API_KEY is not configured.")

    v_id = voice_id or DEFAULT_VOICE_ID
    m_id = model_id or ELEVENLABS_DEFAULT_MODEL
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{v_id}/stream"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": key,
    }
    payload = {
        "text": text.strip(),
        "model_id": m_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }

    with httpx.Client(timeout=45.0) as client:
        with client.stream("POST", url, headers=headers, json=payload) as response:
            if response.status_code != 200:
                error_body = response.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"ElevenLabs TTS failed [{response.status_code}]: {error_body}"
                )
            for chunk in response.iter_bytes(chunk_size=4096):
                if chunk:
                    yield chunk


def generate_elevenlabs_audio(
    text: str,
    voice_id: Optional[str] = None,
    model_id: Optional[str] = None,
) -> Tuple[bytes, float]:
    """
    Generate complete MP3 audio for given text via ElevenLabs Flash v2.5.
    Returns: (mp3_bytes, duration_seconds)
    """
    start_time = time.time()
    accumulated_mp3 = bytearray()

    for chunk in stream_elevenlabs_audio(text, voice_id=voice_id, model_id=model_id):
        accumulated_mp3.extend(chunk)

    word_count = len(text.strip().split())
    # Standard narration pace ~2.5 words/sec (150 words/min)
    estimated_duration = max(1.5, round(word_count / 2.5, 2))
    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info(
        f"Generated ElevenLabs Flash audio ({len(accumulated_mp3)} bytes, ~{estimated_duration}s) in {elapsed_ms}ms"
    )

    return bytes(accumulated_mp3), estimated_duration

