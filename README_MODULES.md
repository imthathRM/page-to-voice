# Page to Voice: Text Processing & Google Gemini TTS Modules

> **Intelligent Audiobook Generation and Listening Platform**  
> Backend Engineering & AI Integration Documentation

---

## 1. Project Overview

**Page to Voice** is a platform that transforms extracted document text (from PDFs, DOCX, scans, and books) into structured, lifelike audiobooks. 

This repository houses the core text processing, narration chunking, and speech synthesis components of the backend.

---

## 2. Assigned Responsibilities

This implementation specifically covers three decoupled, reusable backend components:

1. **Text Cleaning Module** (`page_to_voice.cleaning`): Cleans and normalizes extracted document text, removing artifacts and unwanted control characters while strictly preserving Unicode scripts (English, Tamil, Sinhala), mathematical expressions, and document structure.
2. **Narration Preparation Module** (`page_to_voice.narration`): Splits prose into sentences based on multi-language punctuation rules, formats them into speech-ready chunks with configurable size limits, and preserves chapter/section metadata.
3. **Google Gemini Text-to-Speech (TTS) Module** (`page_to_voice.tts`): Connects to the official Google Gen AI Python SDK (`google-genai`), generates high-fidelity audio from narration chunks, and correctly packages raw PCM/WAV data into standard playable `.wav` audio files.
4. **End-to-End Pipeline** (`page_to_voice.pipeline`): Coordinates the complete flow from raw text to generated audio files with error recovery.

---

## 3. Architecture & Processing Flow

```
                      Raw Extracted Text / Chapters
                                   │
                                   ▼
                 ┌───────────────────────────────────┐
                 │        Text Cleaning Module       │
                 │   - Unicode NFC Normalization     │
                 │   - Strips Control & Null Chars   │
                 │   - Preserves Math, ZWJ/ZWNJ      │
                 └─────────────────┬─────────────────┘
                                   │ Cleaned Text
                                   ▼
                 ┌───────────────────────────────────┐
                 │   Narration Preparation Module    │
                 │   - Multilingual Sentence Split   │
                 │   - Sentence-aware Chunking       │
                 │   - Chapter / Section Preservation│
                 └─────────────────┬─────────────────┘
                                   │ NarrationPlan (Chunks)
                                   ▼
                 ┌───────────────────────────────────┐
                 │       Google Gemini TTS Module    │
                 │   - Official google-genai SDK     │
                 │   - Model: gemini-3.8-flash-tts   │
                 │   - Retry & Rate Limit Handling   │
                 └─────────────────┬─────────────────┘
                                   │ Audio Bytes (PCM / WAV)
                                   ▼
                 ┌───────────────────────────────────┐
                 │       Audio Writer & Validator    │
                 │   - RIFF Header Validation        │
                 │   - PCM-to-WAV Packaging          │
                 │   - Playability Check             │
                 └─────────────────┬─────────────────┘
                                   │
                                   ▼
                   Organized Audio Output (.wav files)
```

---

## 4. Folder Structure

```text
page-to-voice/
│
├── src/
│   └── page_to_voice/
│       ├── __init__.py                     # Package entry point & public exports
│       ├── cleaning/
│       │   ├── __init__.py
│       │   └── text_cleaner.py             # Multi-language text cleaner & Unicode normalizer
│       ├── narration/
│       │   ├── __init__.py
│       │   ├── models.py                   # NarrationChunk, Chapter, NarrationPlan dataclasses
│       │   ├── boundary_detector.py        # Sentence boundary detector for EN, TA, SI
│       │   └── chunker.py                  # Sentence chunker & duration estimator
│       ├── tts/
│       │   ├── __init__.py
│       │   ├── models.py                   # VoiceSettings, TTSConfig, SpeechResult models
│       │   ├── audio_writer.py             # PCM-to-WAV packaging & RIFF validation
│       │   └── gemini_tts.py               # Google Gemini TTS client via google-genai SDK
│       └── pipeline.py                     # Orchestrator (Raw Text -> Clean -> Chunks -> Audio)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                         # Test fixtures, sample texts, synthetic PCM audio
│   ├── test_cleaning.py                    # Unit tests for text cleaning (EN, TA, SI, math, controls)
│   ├── test_narration.py                   # Unit tests for boundaries, chunking, and chapters
│   ├── test_audio_writer.py                # Unit tests for PCM/WAV packaging and validation
│   ├── test_tts_mocked.py                  # Unit tests for Gemini TTS with mocked responses
│   ├── test_pipeline.py                    # Unit tests for full pipeline execution
│   └── test_tts_live.py                    # Live API tests (skipped when GEMINI_API_KEY is unset)
│
├── outputs/                                # Target directory for audio output files
│   └── .gitkeep
│
├── .env.example                            # Template for environment configuration
├── .gitignore                              # Git exclusion rules (venv, secrets, cache, audio)
├── requirements.txt                        # Production & test dependencies
└── README_MODULES.md                       # This documentation guide
```

---

## 5. Python Environment & Setup

The codebase is engineered and verified for **Python 3.14.6** and uses standard-library modules (`unicodedata`, `re`, `wave`, `struct`, `dataclasses`, `pathlib`) for maximum stability without brittle binary extensions.

### Virtual Environment Activation

```powershell
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt)
.\venv\Scripts\activate.bat

# Linux / macOS
source venv/bin/activate
```

---

## 6. Dependency Installation

Dependencies are pinned in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Core libraries:
- `google-genai>=2.34.0`: Official Google Gen AI SDK for Python.
- `python-dotenv>=1.2.0`: Local environment management.
- `pytest>=9.0.0`: Automated test execution framework.

---

## 7. Gemini API Key Configuration

1. Obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/).
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` and set your key:
   ```env
   GEMINI_API_KEY=AIzaSy...your_actual_key...
   GEMINI_TTS_MODEL=gemini-3.8-flash-tts
   DEFAULT_VOICE=Kore
   AUDIO_OUTPUT_DIR=outputs
   ```
4. **Security Notice:** `.env` is listed in `.gitignore`. Never commit API keys to version control. The client will never output or expose keys in logs or exceptions.

---

## 8. Verified Model & Voice Information

Based on the official Google Gen AI documentation ([ai.google.dev/gemini-api/docs/speech-generation](https://ai.google.dev/gemini-api/docs/speech-generation)):

### Verified Models
| Model Identifier | Purpose | Description |
| :--- | :--- | :--- |
| `gemini-3.8-flash-tts` | **Default** | Primary TTS model with high expressiveness, multi-lingual support, and stylistic control. |
| `gemini-3.8-flash-lite-tts` | Fallback | Lower-cost, high-throughput voice generation variant. |
| `gemini-2.5-flash` | Multimodal fallback | General multimodal model supporting `response_modalities=["AUDIO"]`. |
| `gemini-2.0-flash` | Multimodal fallback | Earlier multimodal audio generation endpoint. |

### Verified Prebuilt Voice Personas
The following studio-quality voices are supported by Google Gemini TTS:
- `Kore` (Default, balanced and clear)
- `Puck`
- `Zephyr`
- `Aoede`
- `Fenrir`
- `Charon`
- `Autonoe`
- `Orus`
- `Umbriel`
- `Erinome`
- `Laomedeia`
- `Schedar`

---

## 9. Verified Language Support & Limitations

### 1. English
- **Status:** **Fully Supported (General Availability)**
- Tested with punctuation, initials, abbreviations, decimal numbers, and complex dialogue.

### 2. Tamil (`ta-IN`)
- **Status:** **Supported natively in Gemini 3.8 Flash TTS**
- Unicode block `\u0B80` - `\u0BFF` is preserved.
- Traditional sentence punctuation (Danda `।` / `॥`) and standard punctuation (`.`, `?`, `!`) supported.
- Common Tamil honorifics (`திரு.`, `பேரா.`, `டாக்டர்.`) recognized without false sentence splits.

### 3. Sinhala (`si-LK`)
- **Status:** **Supported natively in Gemini 3.8 Flash TTS (Cloud TTS: Preview)**
- Unicode block `\u0D80` - `\u0DFF` is preserved.
- Zero-Width Joiner (`\u200D` / ZWJ) and Zero-Width Non-Joiner (`\u200C` / ZWNJ) are strictly protected to ensure "Rakaransaya" (ක්‍ර) and "Yansaya" (ක්‍ය) glyphs are not broken.
- Traditional Kunddaliya (`෴`) and modern punctuation (`.`, `?`, `!`) supported.
- Sinhala honorifics (`ආචාර්ය.`, `මහා.`, `ගරු.`) handled cleanly.

---

## 10. Audio Format & Output Specifications

- **Container:** Standard RIFF/WAV (`audio/wav`)
- **Channels:** 1 (Mono)
- **Sample Rate:** 24,000 Hz (24 kHz)
- **Bit Depth:** 16-bit signed PCM (2 bytes per sample, little-endian)
- **PCM Wrapping:** If the Gemini API returns raw headerless PCM bytes (`audio/pcm` or `audio/l16`), `audio_writer.py` generates standard RIFF/WAVE header chunks before saving. Files are fully playable in Windows Media Player, VLC, QuickTime, browser `<audio>` elements, and Audacity.

---

## 11. Module Usage Examples

### Module 1: Text Cleaning

```python
from page_to_voice.cleaning import clean_text

dirty_text = """
  # Chapter 1: Introduction \x00\x08 
  
  Artificial intelligence (AI) has advanced rapidly. \t\t
  It supports English, Tamil (வணக்கம்) and Sinhala (ආයුබෝවන්)!
  
  In physics, E = mc^2 and cost is $150.75.
"""

cleaned = clean_text(dirty_text)
print(cleaned)
```

### Module 2: Narration Preparation

```python
from page_to_voice.narration import prepare_narration, Chapter

# Single document
plan = prepare_narration(text=cleaned, max_chars=1200)
for chunk in plan.chunks:
    print(f"Chunk {chunk.index} ({chunk.word_count} words): {chunk.text[:60]}...")

# Structured chapters
chapters = [
    Chapter(title="Chapter 1", content="First chapter content...", section_title="Part A"),
    Chapter(title="Chapter 2", content="Second chapter content...", section_title="Part B"),
]
chapter_plan = prepare_narration(chapters=chapters, max_chars=1500)
```

### Module 3: Google Gemini TTS

```python
from page_to_voice.tts import GeminiTTS, TTSConfig, VoiceSettings

config = TTSConfig(
    voice_settings=VoiceSettings(
        voice_name="Kore",
        language_code="en-US",
        style_prompt="Narrate clearly and calmly at a natural audiobook pace",
    ),
    output_dir="outputs/audiobooks",
)

tts = GeminiTTS(config=config)
results = tts.generate_speech_for_chunks(plan.chunks)

for res in results:
    if res.status == "success":
        print(f"Generated: {res.audio_path} (Duration: {res.duration_seconds}s)")
```

### End-to-End Pipeline

```python
from page_to_voice.pipeline import process_page_to_voice

result = process_page_to_voice(
    text=dirty_text,
    max_chars_per_chunk=1500,
)

if result.success:
    print(f"Audiobook ready! {len(result.audio_files)} files created.")
    print(f"Total duration: {result.total_duration_seconds} seconds.")
```

---

## 12. Team Integration Guide

This section is prepared for teammates working on Document Extraction, OCR, Frontend, and FastAPI backend.

### Decoupled Integration Pattern

You do not need to rewrite or modify this package when integrating with FastAPI or background workers (Celery/RQ):

```python
# main_backend/routes/audiobook.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

from page_to_voice.pipeline import process_page_to_voice
from page_to_voice.tts.models import TTSConfig, VoiceSettings

router = APIRouter(prefix="/audiobook", tags=["Audiobook"])

class NarrationRequest(BaseModel):
    document_id: str
    extracted_text: str
    voice_name: Optional[str] = "Kore"
    language_code: Optional[str] = "en-US"

@router.post("/generate")
def generate_audiobook(request: NarrationRequest):
    cfg = TTSConfig(
        voice_settings=VoiceSettings(
            voice_name=request.voice_name,
            language_code=request.language_code,
        ),
        output_dir=f"outputs/docs/{request.document_id}",
    )
    
    result = process_page_to_voice(
        text=request.extracted_text,
        tts_config=cfg,
    )
    
    if not result.success:
        raise HTTPException(
            status_code=500, 
            detail=f"Speech synthesis failed for chunks: {result.failed_chunks}"
        )
        
    return {
        "document_id": request.document_id,
        "total_chunks": result.narration_plan.total_chunks,
        "total_duration_seconds": result.total_duration_seconds,
        "audio_files": result.audio_files,
    }
```

---

## 13. Running Automated Tests

Run the complete test suite:

```bash
# Set PYTHONPATH to include src
$env:PYTHONPATH="src"
$env:PYTHONIOENCODING="utf-8"

# Run pytest
pytest -v
```

### Test Suite Breakdown
1. `tests/test_cleaning.py`: Tests English, Tamil, Sinhala, Unicode NFC normalization, ZWJ/ZWNJ preservation, mathematical notation, excess whitespace, control characters, empty input, and large text efficiency.
2. `tests/test_narration.py`: Tests boundary detection, decimals, abbreviations, Tamil danda, Sinhala Kunddaliya, chunk size enforcement, long sentence clause-splitting, chapter metadata, and ordering.
3. `tests/test_audio_writer.py`: Tests PCM-to-WAV wrapping, header validation, MIME sample rate extraction, and error handling.
4. `tests/test_tts_mocked.py`: Tests Gemini TTS responses using mocks, retries on 429 rate limits, partial batch failure preservation, and security.
5. `tests/test_pipeline.py`: Tests end-to-end integration workflow with raw text and chapter objects.
6. `tests/test_tts_live.py`: Real API tests against Gemini. **Automatically skipped** when `GEMINI_API_KEY` is not present, ensuring CI/CD and offline tests never fail unexpectedly.

---

## 14. Known Limitations & Recommendations

1. **TTS API Quotas:** Google Gemini API imposes requests-per-minute (RPM) limits. The client includes exponential backoff retry logic, but for huge books (500+ pages), process chunks with small pauses or run asynchronously through a background queue.
2. **Tamil and Sinhala Live Verification:** Live testing depends on a valid `GEMINI_API_KEY`. In the mock test suite, the entire pipeline is verified; once an API key is set in `.env`, run `pytest tests/test_tts_live.py -v` to perform live audio verification.
3. **Audio File Streaming:** For production web streaming, consider concatenating chunks or serving a playlist manifest (e.g. HLS or standard JSON playlist of `.wav` files).
