import os
import io
import time
import wave
import base64
import uuid
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Generator
from dotenv import load_dotenv
import httpx
from gtts import gTTS

# Ensure environment variables are loaded
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from services.storage import AUDIO_DIR
from services import azure_tts_service
from services import elevenlabs_service

logger = logging.getLogger("tts_service")

# TTS Provider Preference: 'azure', 'elevenlabs', 'gemini', 'gtts'
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "azure").strip().lower()

# Gemini configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_TTS_MODEL = os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")

# Sweet-spot chunk length for high-quality, uninterrupted TTS synthesis
MAX_TTS_CHUNK_CHARS = 1600


def get_available_voices(language: str = "en") -> List[Dict[str, Any]]:
    """
    Return comprehensive list of available voices based on active providers and language.
    Includes badges for Azure Neural, ElevenLabs Flash v2.5, and Gemini TTS.
    """
    norm_lang = azure_tts_service.normalize_language_code(language)
    voices: List[Dict[str, Any]] = []

    # 1. ElevenLabs Flash v2.5 (English primary)
    if norm_lang == "en" and elevenlabs_service.is_elevenlabs_configured():
        for v in elevenlabs_service.get_available_voices():
            voices.append({
                "name": v["name"],
                "gender": v["gender"],
                "label": f"{v['label']} [ElevenLabs Flash]",
                "provider": "elevenlabs",
            })

    # 2. Azure AI Speech Neural Voices (English, Tamil, Sinhala)
    if azure_tts_service.is_azure_configured() or TTS_PROVIDER == "azure":
        az_voices = azure_tts_service.AVAILABLE_AZURE_VOICES.get(norm_lang, [])
        for v in az_voices:
            voices.append({
                "name": v["name"],
                "gender": v["gender"],
                "label": f"{v['label']} [Azure Neural]",
                "provider": "azure",
            })

    # 3. Gemini TTS (English)
    if norm_lang == "en" and GEMINI_API_KEY:
        gemini_voices = [
            {"name": "Puck", "gender": "Male", "label": "Puck [Gemini TTS]", "provider": "gemini"},
            {"name": "Charon", "gender": "Male", "label": "Charon [Gemini TTS]", "provider": "gemini"},
            {"name": "Kore", "gender": "Female", "label": "Kore [Gemini TTS]", "provider": "gemini"},
            {"name": "Fenrir", "gender": "Male", "label": "Fenrir [Gemini TTS]", "provider": "gemini"},
            {"name": "Aoede", "gender": "Female", "label": "Aoede [Gemini TTS]", "provider": "gemini"},
        ]
        voices.extend(gemini_voices)

    # 4. Fallback Google TTS (always available)
    if not voices:
        voices.append({
            "name": "default",
            "gender": "Neutral",
            "label": f"Google TTS ({norm_lang.upper()}) [Standard]",
            "provider": "gtts",
        })

    return voices


def get_audio_cache_key(text: str, language: str, voice_name: str, provider: str) -> str:
    """Generate a deterministic 20-character cache hash for text and narration settings."""
    payload = f"{text.strip()}_{language.lower()}_{voice_name}_{provider}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def get_wav_duration(wav_bytes: bytes) -> float:
    """Calculate duration from WAV header."""
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as r:
            return round(r.getnframes() / float(r.getframerate()), 2)
    except Exception:
        return 0.0


def split_text_into_tts_chunks(text: str, max_chars: int = MAX_TTS_CHUNK_CHARS) -> List[str]:
    """
    Split long text into sentence/paragraph aligned chunks suitable for TTS.
    Avoids cutting words or awkward mid-sentence breaks.
    """
    text = text.strip()
    if not text or len(text) <= max_chars:
        return [text] if text else []

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_len = 0

    for para in paragraphs:
        para_clean = para.strip()
        if not para_clean:
            continue

        if len(para_clean) <= max_chars:
            if current_len + len(para_clean) + 2 <= max_chars:
                current_chunk.append(para_clean)
                current_len += len(para_clean) + 2
            else:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                current_chunk = [para_clean]
                current_len = len(para_clean)
        else:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_len = 0

            import re
            sentences = re.split(r"(?<=[.!?])\s+", para_clean)
            sentence_chunk = []
            sentence_len = 0

            for s in sentences:
                if sentence_len + len(s) + 1 <= max_chars:
                    sentence_chunk.append(s)
                    sentence_len += len(s) + 1
                else:
                    if sentence_chunk:
                        chunks.append(" ".join(sentence_chunk))
                    sentence_chunk = [s]
                    sentence_len = len(s)

            if sentence_chunk:
                chunks.append(" ".join(sentence_chunk))

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return [c for c in chunks if c.strip()]


def call_gemini_tts_single_chunk(
    chunk_text: str,
    voice_name: str = "Puck",
    max_retries: int = 1,
) -> bytes:
    """
    Call Gemini TTS for a single chunk with automatic retry & fast fallback on 429.
    Returns: raw 16-bit 24kHz linear PCM bytes.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_TTS_MODEL}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY,
    }
    data = {
        "contents": [{"parts": [{"text": chunk_text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice_name or "Puck"
                    }
                }
            },
        },
    }

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, headers=headers, json=data)

                if res.status_code == 200:
                    res_json = res.json()
                    candidates = res_json.get("candidates", [])
                    if not candidates:
                        raise RuntimeError("Gemini TTS response contained no candidates.")

                    parts = candidates[0].get("content", {}).get("parts", [])
                    inline_data = None
                    for part in parts:
                        if "inlineData" in part:
                            inline_data = part["inlineData"]
                            break

                    if not inline_data or "data" not in inline_data:
                        raise RuntimeError("No audio data returned by Gemini TTS.")

                    return base64.b64decode(inline_data["data"])

                elif res.status_code in (429, 503):
                    if attempt < max_retries:
                        time.sleep(0.5)
                        continue
                    else:
                        raise RuntimeError(f"Gemini TTS rate limited ({res.status_code})")
                else:
                    raise RuntimeError(f"Gemini TTS request failed [{res.status_code}]: {res.text}")

        except (httpx.TimeoutException, httpx.NetworkError) as net_err:
            last_error = net_err
            if attempt < max_retries:
                time.sleep(0.5)
                continue
            else:
                break
        except Exception as exc:
            last_error = exc
            break

    raise RuntimeError(f"Gemini TTS failed: {last_error}")



def generate_audio_gemini_tts(
    text: str,
    voice_name: str = "Puck",
) -> Tuple[bytes, float]:
    """
    Generate audio via Gemini TTS endpoint.
    Handles long text by breaking into natural chunks and seamlessly stitching linear PCM.
    Returns: (wav_bytes, duration_seconds)
    """
    chunks = split_text_into_tts_chunks(text, max_chars=MAX_TTS_CHUNK_CHARS)
    if not chunks:
        raise ValueError("Cannot synthesize audio from empty text.")

    combined_pcm = bytearray()
    sample_rate = 24000
    channels = 1
    sample_width = 2

    for chunk in chunks:
        pcm_bytes = call_gemini_tts_single_chunk(chunk, voice_name=voice_name)
        combined_pcm.extend(pcm_bytes)

    duration = len(combined_pcm) / (sample_rate * channels * sample_width)

    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(combined_pcm)

    return wav_io.getvalue(), round(duration, 2)


def generate_audio_gtts(text: str, lang: str = "en") -> Tuple[bytes, float]:
    """
    Generate audio via Google Text-to-Speech (gTTS).
    Native support for English ('en'), Tamil ('ta'), and Sinhala ('si').
    Stitches multiple MP3 streams if text exceeds single-request limits.
    Returns: (mp3_bytes, estimated_duration_seconds)
    """
    norm_lang = azure_tts_service.normalize_language_code(lang)
    target_lang = norm_lang

    chunks = split_text_into_tts_chunks(text, max_chars=2500)
    if not chunks:
        raise ValueError("Cannot synthesize audio from empty text.")

    combined_mp3 = bytearray()
    total_words = 0

    for chunk in chunks:
        tts = gTTS(text=chunk, lang=target_lang, slow=False)
        mp3_io = io.BytesIO()
        tts.write_to_fp(mp3_io)
        combined_mp3.extend(mp3_io.getvalue())
        total_words += len(chunk.split())

    rate = 2.2 if target_lang in ("ta", "si") else 2.5
    est_duration = max(2.0, round(total_words / rate, 2))

    return bytes(combined_mp3), est_duration


def resolve_provider_and_voice(
    text: str,
    language: str,
    voice_name: Optional[str] = None,
) -> Tuple[str, str, str]:
    """
    Determine the optimal provider, voice name, and file extension based on language and credentials.
    Returns: (provider_name, voice_name, file_extension)
    """
    norm_lang = azure_tts_service.normalize_language_code(language)
    is_english = (norm_lang == "en")
    pref = os.getenv("TTS_PROVIDER", TTS_PROVIDER).strip().lower()

    # 1. ElevenLabs Flash v2.5 (when explicitly chosen or set as preference for English)
    if (pref == "elevenlabs" or voice_name in [v["name"] for v in elevenlabs_service.AVAILABLE_ELEVENLABS_VOICES]) and elevenlabs_service.is_elevenlabs_configured():
        return "elevenlabs", (voice_name or elevenlabs_service.DEFAULT_VOICE_ID), "mp3"

    # 2. Azure AI Speech (Primary for EN, TA, SI when configured)
    if (pref == "azure" or not pref) and azure_tts_service.is_azure_configured():
        resolved_v = azure_tts_service.resolve_voice_name(norm_lang, voice_name)
        return "azure", resolved_v, "mp3"

    # 3. Gemini TTS (English only)
    if is_english and GEMINI_API_KEY and (pref == "gemini" or not azure_tts_service.is_azure_configured()):
        return "gemini-tts", (voice_name or "Puck"), "wav"

    # 4. Azure Fallback (if key is present even if pref was not azure)
    if azure_tts_service.is_azure_configured():
        resolved_v = azure_tts_service.resolve_voice_name(norm_lang, voice_name)
        return "azure", resolved_v, "mp3"

    # 5. Universal Fallback: gTTS
    return "gtts", "default", "mp3"


def stream_speech_chunks(
    text: str,
    language: str = "en",
    voice_name: Optional[str] = None,
) -> Generator[bytes, None, None]:
    """
    Generator yielding audio bytes in real-time chunks for HTTP streaming.
    Enables instant frontend audio playback without waiting for full chapter completion.
    """
    clean_text = text.strip()
    if not clean_text:
        return

    norm_lang = azure_tts_service.normalize_language_code(language)
    provider, resolved_voice, file_ext = resolve_provider_and_voice(clean_text, norm_lang, voice_name)

    # 1. Check if complete audio is already in cache
    candidate_providers = [provider, "azure", "gemini-tts", "gtts", "elevenlabs"]
    for cand_p in candidate_providers:
        cand_ext = "wav" if cand_p == "gemini-tts" else "mp3"
        cand_key = get_audio_cache_key(clean_text, norm_lang, resolved_voice, cand_p)
        cached_filepath = AUDIO_DIR / f"audio_{cand_key}.{cand_ext}"
        if cached_filepath.exists() and cached_filepath.stat().st_size > 500:
            logger.info(f"Streaming from cached audio: {cached_filepath.name}")
            with open(cached_filepath, "rb") as f:
                while True:
                    chunk = f.read(16384)
                    if not chunk:
                        break
                    yield chunk
            return


    # 2. Live streaming from provider
    if provider == "elevenlabs" and elevenlabs_service.is_elevenlabs_configured():
        try:
            yield from elevenlabs_service.stream_elevenlabs_audio(clean_text, voice_id=resolved_voice)
            return
        except Exception as e:
            logger.warning(f"ElevenLabs streaming failed ({e}), falling back to Azure/Gemini...")

    if provider == "azure" and azure_tts_service.is_azure_configured():
        try:
            yield from azure_tts_service.stream_azure_audio_chunks(clean_text, voice_name=resolved_voice, language=norm_lang)
            return
        except Exception as e:
            logger.warning(f"Azure streaming failed ({e}), falling back to gTTS...")

    # Fallback to complete generation then chunked yield
    res = generate_speech(clean_text, language=norm_lang, voice_name=voice_name)
    with open(res["filepath"], "rb") as f:
        while True:
            chunk = f.read(16384)
            if not chunk:
                break
            yield chunk


def generate_speech(
    text: str,
    language: str = "en",
    voice_name: Optional[str] = None,
    force_regenerate: bool = False,
) -> Dict[str, Any]:
    """
    Unified high-performance TTS dispatch with:
    - Multi-provider support (ElevenLabs Flash, Azure AI Speech, Gemini TTS, gTTS).
    - Intelligent caching by deterministic hash (0ms cache hits).
    - High voice fidelity across English, Tamil, and Sinhala.
    """
    if not text or not text.strip():
        raise ValueError("Cannot generate speech from empty text.")

    clean_snippet = text.strip()
    norm_lang = azure_tts_service.normalize_language_code(language)
    is_english = (norm_lang == "en")

    provider, resolved_voice, file_ext = resolve_provider_and_voice(clean_snippet, norm_lang, voice_name)

    # 1. Check Cache across candidate providers
    candidate_providers = [provider, "azure", "gemini-tts", "gtts", "elevenlabs"]
    for cand_p in candidate_providers:
        cand_ext = "wav" if cand_p == "gemini-tts" else "mp3"
        cand_key = get_audio_cache_key(clean_snippet, norm_lang, resolved_voice, cand_p)
        cand_file = AUDIO_DIR / f"audio_{cand_key}.{cand_ext}"
        if not force_regenerate and cand_file.exists() and cand_file.stat().st_size > 500:
            logger.info(f"Audio cache HIT for key {cand_key} ({cand_file.name}). Reusing audio.")
            duration = 0.0
            if cand_ext == "wav":
                try:
                    with wave.open(str(cand_file), "rb") as r:
                        duration = round(r.getnframes() / float(r.getframerate()), 2)
                except Exception:
                    duration = 5.0
            else:
                word_count = len(clean_snippet.split())
                duration = max(2.0, round(word_count / 2.3, 2))

            return {
                "filename": cand_file.name,
                "filepath": str(cand_file),
                "audio_url": f"/api/audio/{cand_file.name}",
                "duration_seconds": duration,
                "format": cand_ext,
                "provider": cand_p,
                "language": norm_lang,
                "voice_name": resolved_voice,
                "cached": True,
                "generation_time_ms": 0,
            }

    # 2. Live Synthesis

    start_time = time.time()
    audio_bytes = None
    duration = 0.0
    actual_provider = provider

    # Try ElevenLabs Flash v2.5
    if provider == "elevenlabs" and elevenlabs_service.is_elevenlabs_configured():
        try:
            audio_bytes, duration = elevenlabs_service.generate_elevenlabs_audio(clean_snippet, voice_id=resolved_voice)
            actual_provider = "elevenlabs"
            file_ext = "mp3"
        except Exception as el_err:
            logger.warning(f"ElevenLabs TTS failed: {el_err}. Falling back to Azure/Gemini...")
            provider = "azure"

    # Try Azure AI Speech
    if provider == "azure":
        if azure_tts_service.is_azure_configured():
            try:
                audio_bytes, duration = azure_tts_service.generate_azure_audio(
                    clean_snippet,
                    voice_name=resolved_voice,
                    language=norm_lang,
                )
                actual_provider = "azure"
                file_ext = "mp3"
            except Exception as az_err:
                logger.warning(f"Azure TTS failed: {az_err}. Falling back to Gemini/gTTS...")
                provider = "gemini-tts" if (is_english and GEMINI_API_KEY) else "gtts"
        else:
            provider = "gemini-tts" if (is_english and GEMINI_API_KEY) else "gtts"

    # Try Gemini TTS
    if provider == "gemini-tts":
        try:
            audio_bytes, duration = generate_audio_gemini_tts(clean_snippet, voice_name=resolved_voice)
            actual_provider = "gemini-tts"
            file_ext = "wav"
        except Exception as gemini_err:
            logger.warning(f"Gemini TTS failed: {gemini_err}. Falling back to gTTS...")
            provider = "gtts"

    # Universal Fallback: gTTS
    if audio_bytes is None:
        audio_bytes, duration = generate_audio_gtts(clean_snippet, lang=norm_lang)
        actual_provider = "gtts"
        file_ext = "mp3"

    generation_time_ms = int((time.time() - start_time) * 1000)

    # Save to disk cache
    final_cache_key = get_audio_cache_key(clean_snippet, norm_lang, resolved_voice, actual_provider)
    final_filename = f"audio_{final_cache_key}.{file_ext}"
    final_filepath = AUDIO_DIR / final_filename

    with open(final_filepath, "wb") as f:
        f.write(audio_bytes)

    logger.info(
        f"Generated audio via {actual_provider} in {generation_time_ms}ms ({duration}s duration) -> {final_filename}"
    )

    return {
        "filename": final_filename,
        "filepath": str(final_filepath),
        "audio_url": f"/api/audio/{final_filename}",
        "duration_seconds": duration,
        "format": file_ext,
        "provider": actual_provider,
        "language": norm_lang,
        "voice_name": resolved_voice,
        "cached": False,
        "generation_time_ms": generation_time_ms,
    }
