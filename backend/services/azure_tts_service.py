import os
import io
import time
import logging
import threading
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Generator
from dotenv import load_dotenv

# Ensure environment variables are loaded
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger("azure_tts_service")

# Lazy import flag for speechsdk
_speechsdk = None

# Thread-safe synthesizer instance caching
_synthesizer_pool: Dict[str, Any] = {}
_pool_lock = threading.Lock()


def get_speech_sdk():
    global _speechsdk
    if _speechsdk is None:
        try:
            import azure.cognitiveservices.speech as speechsdk
            _speechsdk = speechsdk
        except ImportError as e:
            logger.error(f"azure-cognitiveservices-speech is not installed: {e}")
            raise RuntimeError(
                "Microsoft Azure Speech SDK is not installed. Run 'pip install azure-cognitiveservices-speech'."
            )
    return _speechsdk


# Azure Speech configuration
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "").strip()
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "eastus").strip()
AZURE_SPEECH_ENDPOINT = os.getenv("AZURE_SPEECH_ENDPOINT", "").strip()

# Default Neural Voices for English, Tamil, and Sinhala
DEFAULT_AZURE_VOICES: Dict[str, str] = {
    "en": os.getenv("AZURE_SPEECH_VOICE_EN", "en-US-JennyNeural").strip(),
    "ta": os.getenv("AZURE_SPEECH_VOICE_TA", "ta-IN-PallaviNeural").strip(),
    "si": os.getenv("AZURE_SPEECH_VOICE_SI", "si-LK-ThiliniNeural").strip(),
}

# Curated catalog of available voices with metadata
AVAILABLE_AZURE_VOICES: Dict[str, List[Dict[str, str]]] = {
    "en": [
        {"name": "en-US-JennyNeural", "gender": "Female", "label": "Jenny (US English, Neural)", "locale": "en-US"},
        {"name": "en-US-GuyNeural", "gender": "Male", "label": "Guy (US English, Neural)", "locale": "en-US"},
        {"name": "en-US-AriaNeural", "gender": "Female", "label": "Aria (US English, Neural)", "locale": "en-US"},
        {"name": "en-GB-SoniaNeural", "gender": "Female", "label": "Sonia (UK English, Neural)", "locale": "en-GB"},
    ],
    "ta": [
        {"name": "ta-IN-PallaviNeural", "gender": "Female", "label": "Pallavi (India Tamil, Neural)", "locale": "ta-IN"},
        {"name": "ta-IN-ValluvarNeural", "gender": "Male", "label": "Valluvar (India Tamil, Neural)", "locale": "ta-IN"},
        {"name": "ta-LK-SaranyaNeural", "gender": "Female", "label": "Saranya (Sri Lanka Tamil, Neural)", "locale": "ta-LK"},
        {"name": "ta-LK-KumarNeural", "gender": "Male", "label": "Kumar (Sri Lanka Tamil, Neural)", "locale": "ta-LK"},
    ],
    "si": [
        {"name": "si-LK-ThiliniNeural", "gender": "Female", "label": "Thilini (Sri Lanka Sinhala, Neural)", "locale": "si-LK"},
        {"name": "si-LK-SameeraNeural", "gender": "Male", "label": "Sameera (Sri Lanka Sinhala, Neural)", "locale": "si-LK"},
    ],
}


def is_azure_configured() -> bool:
    """Return True if valid Azure Speech credentials are configured in the environment."""
    key = os.getenv("AZURE_SPEECH_KEY", AZURE_SPEECH_KEY).strip()
    region = os.getenv("AZURE_SPEECH_REGION", AZURE_SPEECH_REGION).strip()
    endpoint = os.getenv("AZURE_SPEECH_ENDPOINT", AZURE_SPEECH_ENDPOINT).strip()
    return bool(key and (region or endpoint))


def normalize_language_code(lang: Optional[str]) -> str:
    """Normalize language name or code to 'en', 'ta', or 'si'."""
    if not lang:
        return "en"
    l = lang.strip().lower()
    if l.startswith("ta") or l == "tamil":
        return "ta"
    elif l.startswith("si") or l == "sinhala":
        return "si"
    return "en"


def resolve_voice_name(language: str, requested_voice: Optional[str] = None) -> str:
    """
    Select an appropriate Azure Neural voice.
    Honors requested_voice if provided and non-empty, otherwise defaults per language.
    """
    norm_lang = normalize_language_code(language)
    if requested_voice and requested_voice.strip():
        return requested_voice.strip()
    return DEFAULT_AZURE_VOICES.get(norm_lang, "en-US-JennyNeural")


def split_text_for_azure(text: str, max_chars: int = 2800) -> List[str]:
    """
    Split text into sentence/paragraph aligned chunks suitable for Azure Speech synthesis.
    Keeps paragraphs and sentences intact to preserve natural narration cadence.
    """
    text = text.strip()
    if not text or len(text) <= max_chars:
        return [text] if text else []

    paragraphs = text.split("\n\n")
    chunks: List[str] = []
    current_chunk: List[str] = []
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
            sentence_chunk: List[str] = []
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


def create_azure_speech_config(voice_name: str):
    """Create and return a configured speechsdk.SpeechConfig for Azure TTS."""
    speechsdk = get_speech_sdk()

    key = os.getenv("AZURE_SPEECH_KEY", AZURE_SPEECH_KEY).strip()
    region = os.getenv("AZURE_SPEECH_REGION", AZURE_SPEECH_REGION).strip()
    endpoint = os.getenv("AZURE_SPEECH_ENDPOINT", AZURE_SPEECH_ENDPOINT).strip()

    if not key:
        raise ValueError("AZURE_SPEECH_KEY environment variable is not set.")

    if endpoint:
        speech_config = speechsdk.SpeechConfig(endpoint=endpoint, subscription=key)
    else:
        speech_config = speechsdk.SpeechConfig(subscription=key, region=region or "eastus")

    # Set high quality MP3 output format (24kHz 160kbps mono)
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio24Khz160KBitRateMonoMp3
    )
    speech_config.speech_synthesis_voice_name = voice_name
    return speech_config


def get_cached_synthesizer(voice_name: str):
    """
    Get or create a warm, cached SpeechSynthesizer for the given voice.
    Reusing synthesizer instances eliminates redundant TLS handshakes.
    """
    speechsdk = get_speech_sdk()
    with _pool_lock:
        if voice_name not in _synthesizer_pool:
            speech_config = create_azure_speech_config(voice_name)
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
            _synthesizer_pool[voice_name] = synthesizer
        return _synthesizer_pool[voice_name]


def synthesize_azure_chunk(
    chunk_text: str,
    voice_name: str,
    max_retries: int = 2,
) -> Tuple[bytes, float]:
    """
    Synthesize a single text chunk using pooled Azure Speech SDK synthesizer.
    Returns: (mp3_bytes, duration_seconds)
    """
    speechsdk = get_speech_sdk()
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            synthesizer = get_cached_synthesizer(voice_name)
            result = synthesizer.speak_text_async(chunk_text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_bytes = result.audio_data
                duration = 0.0
                if hasattr(result, "audio_duration") and result.audio_duration:
                    duration = round(result.audio_duration.total_seconds(), 2)
                else:
                    word_count = len(chunk_text.split())
                    duration = max(1.0, round(word_count / 2.5, 2))
                return audio_bytes, duration

            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = speechsdk.SpeechSynthesisCancellationDetails(result)
                error_detail = cancellation.error_details or "Synthesis canceled"
                last_error = RuntimeError(f"Azure Speech Error: {cancellation.reason} - {error_detail}")
                logger.warning(
                    f"Azure Speech attempt {attempt + 1}/{max_retries + 1} canceled: {error_detail}"
                )

                # Reset cached instance on connection/token error
                with _pool_lock:
                    _synthesizer_pool.pop(voice_name, None)

                if attempt < max_retries:
                    wait_sec = 1.0 * (2 ** attempt)
                    time.sleep(wait_sec)
                    continue
                else:
                    raise last_error

            else:
                last_error = RuntimeError(f"Unexpected Azure synthesis reason: {result.reason}")
                if attempt < max_retries:
                    time.sleep(1.0)
                    continue
                raise last_error

        except Exception as exc:
            last_error = exc
            logger.warning(f"Azure Speech synthesis exception (attempt {attempt + 1}): {exc}")
            with _pool_lock:
                _synthesizer_pool.pop(voice_name, None)
            if attempt < max_retries:
                time.sleep(1.0 * (2 ** attempt))
            else:
                raise last_error

    raise last_error or RuntimeError("Azure TTS synthesis failed.")


def stream_azure_audio_chunks(
    text: str,
    voice_name: Optional[str] = None,
    language: str = "en",
) -> Generator[bytes, None, None]:
    """
    Stream MP3 audio chunks in real-time as they are synthesized.
    Yields chunks immediately so playback can begin without waiting for the full chapter.
    """
    clean_text = text.strip()
    if not clean_text:
        return

    norm_lang = normalize_language_code(language)
    selected_voice = resolve_voice_name(norm_lang, voice_name)
    chunks = split_text_for_azure(clean_text, max_chars=2800)

    for chunk in chunks:
        mp3_bytes, _ = synthesize_azure_chunk(chunk, voice_name=selected_voice)
        yield mp3_bytes


def generate_azure_audio(
    text: str,
    voice_name: Optional[str] = None,
    language: str = "en",
) -> Tuple[bytes, float]:
    """
    Generate complete MP3 audio for given text via Microsoft Azure Speech.
    Splits long text into manageable chunks and concatenates MP3 output frames seamlessly.
    
    Returns:
        (mp3_bytes: bytes, total_duration_seconds: float)
    """
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("Cannot synthesize audio from empty text.")

    norm_lang = normalize_language_code(language)
    selected_voice = resolve_voice_name(norm_lang, voice_name)
    logger.info(f"Synthesizing with Azure AI Speech: voice='{selected_voice}', lang='{norm_lang}', length={len(clean_text)} chars")

    chunks = split_text_for_azure(clean_text, max_chars=2800)
    if not chunks:
        raise ValueError("No valid text chunks found for synthesis.")

    combined_mp3 = bytearray()
    total_duration = 0.0

    for i, chunk in enumerate(chunks):
        chunk_mp3, chunk_dur = synthesize_azure_chunk(chunk, voice_name=selected_voice)
        combined_mp3.extend(chunk_mp3)
        total_duration += chunk_dur

    return bytes(combined_mp3), round(total_duration, 2)
