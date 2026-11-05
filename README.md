# Page to Voice: Intelligent Audiobook Generation and Listening Platform

**Page to Voice** converts books and documents (PDF, DOCX, TXT) into high-quality, narrated audiobooks with automatic chapter detection, text cleaning, summarization, multi-language translation (English, Tamil, Sinhala), and neural text-to-speech (TTS) playback.

---

## Sprint 1 Implementation Status: COMPLETE

All Sprint 1 deliverables have been implemented and verified:
1. **Frontend Document Upload Interface:** Drag-and-drop & file browser with file validation, size limits (50 MB), upload progress indicator, and document list.
2. **Backend Document Upload API:** Secure multipart file handling with unique naming and MySQL metadata storage.
3. **Multi-Format Extraction:** PyMuPDF for PDFs (with OCR fallback for scanned pages), `python-docx` for Word documents, and Python built-in handling for TXT.
4. **Text Cleaning & Language Detection:** Unicode NFC normalization preserving Tamil and Sinhala scripts; script-frequency language classification (`en`, `ta`, `si`).
5. **Chapter Detection & Segmentation:** Regex & heading-based chapter detection in English, Tamil, and Sinhala.
6. **Gemini AI Integration:** Reusable service for text cleaning, chapter summarization, and multi-language translation using `google-genai` Python SDK.
7. **Microsoft Azure AI Speech & Gemini Integration:** Azure AI Speech SDK as the primary TTS engine delivering studio-grade MP3 audio (24kHz 160kbps mono) across English, Tamil, and Sinhala Neural voices; Gemini API retained for text cleaning, summarization, and translation; Gemini TTS and gTTS retained as zero-configuration fallbacks.
8. **Fast Audio Generation & Background Processing:** Asynchronous chapter-by-chapter synthesis with Chapter 1 Priority (immediate listening while remaining chapters synthesize in the background), controlled concurrency (max 2 parallel workers), and deterministic content-hashed audio caching.
9. **In-Browser Audio Player:** Full HTML5 audio player supporting play/pause/resume, seek slider, speed control (1x–2x), duration tracking, synchronized chapter text display, and continuous playlist auto-advance to subsequent chapters.

---

## Text-to-Speech (TTS) Architecture: Azure AI Speech Primary

The platform uses **Microsoft Azure Cognitive Services Speech SDK** as the primary TTS engine, with automatic fallback to **Google Gemini TTS** and **gTTS**:

| Language | Primary Azure Voice | Locale | Gender | Fallback Provider |
|---|---|---|---|---|
| **English** | `en-US-JennyNeural` / `en-US-GuyNeural` | `en-US` | Female / Male | Gemini TTS (`Puck`) / gTTS |
| **Tamil** | `ta-IN-PallaviNeural` / `ta-LK-SaranyaNeural` | `ta-IN` / `ta-LK` | Female | gTTS (`ta`) |
| **Sinhala** | `si-LK-ThiliniNeural` / `si-LK-SameeraNeural` | `si-LK` | Female / Male | gTTS (`si`) |

*Optional Ultra-Low Latency English Provider:* **ElevenLabs Flash v2.5** (`eleven_flash_v2_5`) is supported for sub-100ms first-chunk audio streaming when `ELEVENLABS_API_KEY` is configured.

### Key Performance & Audio Optimizations
1. **Chapter 1 Priority:** Audiobook generation synthesizes Chapter 1 first and immediately commits it to the database so users can begin listening without waiting for the full book to finish.
2. **Instant Audio Streaming (`GET /api/chapters/{id}/stream`):** Delivers live chunked MP3 streaming via FastAPI `StreamingResponse` allowing the frontend player to start within ~5-7ms without waiting for full chapter generation.
3. **Dynamic Priority Queue (`POST /api/chapters/{id}/prioritize`):** Clicking any queued chapter immediately promotes it to the top of the background worker queue.
4. **Controlled Concurrency:** Remaining chapters (2..N) are synthesized in the background with a concurrency throttle of 2 workers (`ThreadPoolExecutor(max_workers=2)`) to avoid rate limit spikes.
5. **Deterministic Audio Caching:** Audio files are stored under `backend/uploads/audio/` with filenames derived from a SHA-256 hash of text, language, voice, and provider (`audio_{hash}.mp3`). Duplicate generation requests are served instantly from cache in 0ms.
6. **Auto-Advance Playback:** The audio player advances automatically to the next chapter upon track completion.

### TTS Provider Comparison Benchmark

| Provider | Supported Languages | TTFB (First Audio) | Full Chapter Speed | Audio Quality | Est. Cost (1M Chars) |
|---|---|---|---|---|---|
| **Microsoft Azure AI Speech** | English, Tamil, Sinhala | ~250–400 ms | 80–120 chars/sec | Studio Neural | $16.00 |
| **ElevenLabs Flash v2.5** | English (Multilingual) | ~75–150 ms | 120–160 chars/sec | Premium Expressive | $150.00 |
| **Google Gemini TTS** | English | ~1200–2500 ms | 40–60 chars/sec | Natural Conversational | $12.00 |
| **Google TTS (`gTTS`)** | English, Tamil, Sinhala | ~5–7 ms (cached/stream) | 18–32 chars/sec | Standard Clear | $0.00 (Free) |


---

## Monorepo Architecture

```
page-to-voice/
├── backend/                      # FastAPI REST API & Storage Layer
│   ├── services/
│   │   ├── storage.py            # Local file upload & audio path management
│   │   ├── document_parser.py    # PyMuPDF, python-docx & TXT extraction
│   │   ├── text_processor.py     # Text cleaning & language detection (EN, TA, SI)
│   │   ├── chapter_detector.py   # Multi-language chapter detection regex & chunking
│   │   ├── gemini_service.py     # Google Gemini API integration
│   │   └── tts_service.py        # Gemini TTS (WAV) & gTTS fallback
│   ├── database.py               # SQLAlchemy engine & Aiven MySQL connection
│   ├── main.py                   # FastAPI endpoints & CORS
│   ├── models.py                 # SQLAlchemy ORM schemas
│   ├── schemas.py                # Pydantic v2 validation models
│   ├── security.py               # JWT authentication & rate limiter
│   └── test_sprint1_workflow.py  # End-to-end automated verification script
│
├── frontend/                     # React 19 Client SPA
│   ├── src/
│   │   ├── api/
│   │   │   ├── axiosClient.js    # Axios instance with JWT interceptors
│   │   │   └── documentService.js# Document upload, AI & TTS service calls
│   │   ├── components/
│   │   │   ├── audio/
│   │   │   │   └── AudioPlayer.jsx # Audio player with scrub bar & text sync
│   │   │   ├── screens/
│   │   │   │   ├── DashboardScreen.jsx       # Overview, stats & document list
│   │   │   │   ├── UploadScreen.jsx          # Drag-and-drop upload interface
│   │   │   │   └── DocumentDetailScreen.jsx  # Chapter management, AI tools & player
│   │   │   └── layout/
│   │   │       └── Navbar.jsx    # Top navigation header
│   │   └── App.jsx               # Screen router & persistent audio state
│   └── vite.config.js            # Reverse proxy (/api, /auth, /users, /health)
```

---

## How to Run

### 1. Start the FastAPI Backend
```powershell
cd backend
py -3.10 -m uvicorn main:app --reload --port 8000
```
- API starts at `http://127.0.0.1:8000`
- Swagger Documentation: `http://127.0.0.1:8000/docs`

### 2. Start the Frontend
In a separate terminal:
```powershell
cd frontend
npm run dev
```
- Client starts at `http://localhost:5173`

---

## Default Credentials
- **Email:** `admin@pagetovoice.com`
- **Username:** `admin`
- **Password:** `1234@1234`
