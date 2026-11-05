from contextlib import asynccontextmanager
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import threading
import concurrent.futures
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, desc


from database import engine, Base, get_db, SessionLocal
import models
import schemas
from security import (
    get_password_hash,
    verify_password,
    verify_dummy_password,
    create_access_token,
    get_current_user,
    login_rate_limiter,
)
from services.storage import (
    save_uploaded_file,
    get_audio_filepath,
    AUDIO_DIR,
)
from services.document_parser import extract_document_text
from services.text_processor import detect_language, clean_text
from services.chapter_detector import detect_chapters
from services import gemini_service, tts_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pagetovoice")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to ensure DB tables are created on startup."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"Database initialization warning on startup: {e}")
    yield


app = FastAPI(
    title="Page to Voice API",
    description="Intelligent Audiobook Generation and Listening Platform API with Hardened Security",
    version="1.2.0",
    lifespan=lifespan,
)

# OWASP Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, taking proxy headers into account."""
    if not request:
        return "127.0.0.1"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


# ==========================================
# SYSTEM & AUTHENTICATION ENDPOINTS
# ==========================================

@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint that verifies database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "service": "Page to Voice API",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(exc)}",
        )


@app.post(
    "/auth/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user with strong password validation."""
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    if db.query(models.User).filter(models.User.username == user_in.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken",
        )

    hashed_password = get_password_hash(user_in.password)
    db_user = models.User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_password,
        role=models.UserRole.USER,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"New user registered: id={db_user.id}, email={db_user.email}")
    return db_user


@app.post(
    "/auth/login",
    response_model=schemas.Token,
    tags=["Authentication"],
)
def login(
    credentials: schemas.UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Hardened authentication endpoint with brute-force protection.
    Supports login by username or email.
    """
    client_ip = get_client_ip(request)
    identifier = (credentials.email or credentials.username or "").strip().lower()
    ip_key = f"ip:{client_ip}"
    user_key = f"user:{identifier}"

    is_ip_locked, ip_rem = login_rate_limiter.is_locked(ip_key)
    if is_ip_locked:
        logger.warning(f"Blocked login attempt from locked IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts from your IP. Temporarily locked for {max(1, ip_rem // 60)} minute(s).",
            headers={"Retry-After": str(ip_rem)},
        )

    is_user_locked, user_rem = login_rate_limiter.is_locked(user_key)
    if is_user_locked:
        logger.warning(f"Blocked login attempt for locked account: {identifier} from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to multiple failed login attempts. Try again in {max(1, user_rem // 60)} minute(s).",
            headers={"Retry-After": str(user_rem)},
        )

    user = (
        db.query(models.User)
        .filter(
            (models.User.email == identifier)
            | (models.User.username == identifier)
        )
        .first()
    )

    if not user:
        verify_dummy_password(credentials.password)
        login_rate_limiter.record_failure(ip_key)
        login_rate_limiter.record_failure(user_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(credentials.password, user.password_hash):
        login_rate_limiter.record_failure(ip_key)
        login_rate_limiter.record_failure(user_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended",
        )

    login_rate_limiter.record_success(ip_key)
    login_rate_limiter.record_success(user_key)

    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token, expires_in = create_access_token(
        data={"sub": user.email, "username": user.username, "role": role_val}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@app.get(
    "/users/me",
    response_model=schemas.UserResponse,
    tags=["Users"],
)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    """Protected route returning details of the currently authenticated user."""
    return current_user


# ==========================================
# DOCUMENT UPLOAD & MANAGEMENT ENDPOINTS
# ==========================================

def get_document_status(doc: models.Document) -> str:
    """Helper to derive processing status for a document."""
    if doc.processing_jobs:
        latest_job = sorted(doc.processing_jobs, key=lambda j: j.created_at, reverse=True)[0]
        return latest_job.status.value if hasattr(latest_job.status, "value") else str(latest_job.status)
    return "uploaded"


@app.post(
    "/api/documents/upload",
    response_model=schemas.DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Receive uploaded document (PDF, DOCX, TXT), validate size/extension,
    safely save to disk, and store metadata in MySQL associated with current user.
    """
    # Save file safely
    stored_filename, absolute_path, file_size = await save_uploaded_file(file)
    ext = Path(file.filename).suffix.lower().lstrip(".")
    doc_title = Path(file.filename).stem.replace("_", " ").title()

    # Determine mode: book if large or PDF/DOCX, else document
    doc_mode = models.DocumentMode.BOOK if ext in ("pdf", "docx") else models.DocumentMode.DOCUMENT

    new_doc = models.Document(
        user_id=current_user.id,
        title=doc_title,
        file_type=ext,
        source_file_url=absolute_path,
        mode=doc_mode,
        source_language="en",
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # Create initial ProcessingJob entry (pending)
    job = models.ProcessingJob(
        document_id=new_doc.id,
        job_type="text_extraction",
        status=models.JobStatus.PENDING,
    )
    db.add(job)
    db.commit()

    logger.info(f"User {current_user.id} uploaded document #{new_doc.id} ({doc_title})")

    return schemas.DocumentResponse(
        id=new_doc.id,
        user_id=new_doc.user_id,
        title=new_doc.title,
        file_type=new_doc.file_type,
        source_file_url=new_doc.source_file_url,
        mode=new_doc.mode.value if hasattr(new_doc.mode, "value") else str(new_doc.mode),
        source_language=new_doc.source_language,
        target_language=new_doc.target_language,
        status="uploaded",
        created_at=new_doc.created_at,
        chapter_count=0,
    )


@app.get(
    "/api/documents",
    response_model=List[schemas.DocumentResponse],
    tags=["Documents"],
)
def list_documents(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all documents owned by the authenticated user."""
    docs = (
        db.query(models.Document)
        .filter(models.Document.user_id == current_user.id)
        .order_by(desc(models.Document.created_at))
        .all()
    )

    result = []
    for d in docs:
        status_val = get_document_status(d)
        result.append(
            schemas.DocumentResponse(
                id=d.id,
                user_id=d.user_id,
                title=d.title,
                file_type=d.file_type,
                source_file_url=d.source_file_url,
                mode=d.mode.value if hasattr(d.mode, "value") else str(d.mode),
                source_language=d.source_language,
                target_language=d.target_language,
                status=status_val,
                created_at=d.created_at,
                chapter_count=len(d.chapters) if d.chapters else 0,
            )
        )
    return result


@app.get(
    "/api/documents/{document_id}",
    response_model=schemas.DocumentDetailResponse,
    tags=["Documents"],
)
def get_document(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full details and chapters of a specific document."""
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.user_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    status_val = get_document_status(doc)
    latest_error = None
    if doc.processing_jobs:
        latest_job = sorted(doc.processing_jobs, key=lambda j: j.created_at, reverse=True)[0]
        latest_error = latest_job.error_message

    chapters_resp = [
        schemas.ChapterResponse(
            id=c.id,
            document_id=c.document_id,
            chapter_number=c.chapter_number,
            title=c.title,
            original_text=c.original_text,
            processed_text=c.processed_text,
            audio_file_url=c.audio_file_url,
            duration_seconds=c.duration_seconds,
            created_at=c.created_at,
        )
        for c in sorted(doc.chapters, key=lambda x: x.chapter_number)
    ]

    return schemas.DocumentDetailResponse(
        id=doc.id,
        user_id=doc.user_id,
        title=doc.title,
        file_type=doc.file_type,
        source_file_url=doc.source_file_url,
        mode=doc.mode.value if hasattr(doc.mode, "value") else str(doc.mode),
        source_language=doc.source_language,
        target_language=doc.target_language,
        status=status_val,
        created_at=doc.created_at,
        chapter_count=len(chapters_resp),
        chapters=chapters_resp,
        error_message=latest_error,
    )


@app.post(
    "/api/documents/{document_id}/process",
    response_model=schemas.DocumentProcessResponse,
    tags=["Documents"],
)
def process_document(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger full extraction pipeline:
    1. Parse document text (PyMuPDF / python-docx / built-in file handling + OCR fallback)
    2. Detect source language (English, Tamil, Sinhala)
    3. Detect chapter structure and boundaries
    4. Store chapters and clean text separately in MySQL
    5. Update processing status to completed or failed
    """
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.user_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Update or create processing job
    job = models.ProcessingJob(
        document_id=doc.id,
        job_type="extraction_and_chapters",
        status=models.JobStatus.PROCESSING,
    )
    db.add(job)
    db.commit()

    try:
        # 1. Text extraction
        parsed = extract_document_text(doc.source_file_url)
        if not parsed.full_text or not parsed.full_text.strip():
            raise ValueError("No text could be extracted from this document.")

        # 2. Language detection
        detected_lang, scores = detect_language(parsed.full_text)
        doc.source_language = detected_lang

        # 3. Chapter detection
        chapters_data = detect_chapters(
            parsed.full_text,
            headings=parsed.headings,
            document_title=doc.title,
        )

        # 4. Remove existing chapters if re-processing
        db.query(models.Chapter).filter(models.Chapter.document_id == doc.id).delete()

        for chap in chapters_data:
            db_chap = models.Chapter(
                document_id=doc.id,
                chapter_number=chap["chapter_number"],
                title=chap["title"],
                original_text=chap["original_text"],
                processed_text=chap["processed_text"],
                duration_seconds=0.0,
            )
            db.add(db_chap)

        job.status = models.JobStatus.COMPLETED
        job.error_message = None
        db.commit()

        logger.info(
            f"Document #{doc.id} processed successfully: {len(chapters_data)} chapters, language='{detected_lang}'"
        )

        return schemas.DocumentProcessResponse(
            document_id=doc.id,
            status="completed",
            message=f"Document processed successfully into {len(chapters_data)} chapter(s).",
            detected_language=detected_lang,
            chapter_count=len(chapters_data),
        )

    except Exception as exc:
        db.rollback()
        job.status = models.JobStatus.FAILED
        job.error_message = str(exc)
        db.commit()
        logger.error(f"Failed to process document #{doc.id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(exc)}",
        )


@app.get(
    "/api/documents/{document_id}/chapters",
    response_model=List[schemas.ChapterResponse],
    tags=["Documents"],
)
def list_chapters(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all chapters for a specific document."""
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.user_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    chapters = (
        db.query(models.Chapter)
        .filter(models.Chapter.document_id == document_id)
        .order_by(models.Chapter.chapter_number.asc())
        .all()
    )

    return chapters


# ==========================================
# GEMINI AI SERVICES (CLEAN, SUMMARIZE, TRANSLATE)
# ==========================================

@app.post(
    "/api/ai/clean-text",
    response_model=schemas.CleanTextResponse,
    tags=["AI Services"],
)
def clean_text_endpoint(
    req: schemas.CleanTextRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clean and optimize text for voice narration using Gemini AI."""
    cleaned = gemini_service.clean_text_for_narration(req.text, language=req.language or "en")

    # If chapter_id was provided, update chapter's processed_text
    if req.chapter_id:
        chap = db.query(models.Chapter).filter(models.Chapter.id == req.chapter_id).first()
        if chap:
            chap.processed_text = cleaned
            db.commit()

    return schemas.CleanTextResponse(cleaned_text=cleaned, chapter_id=req.chapter_id)


@app.post(
    "/api/ai/summarize",
    response_model=schemas.SummarizeResponse,
    tags=["AI Services"],
)
def summarize_endpoint(
    req: schemas.SummarizeRequest,
    current_user: models.User = Depends(get_current_user),
):
    """Generate concise chapter summary using Gemini AI."""
    summary = gemini_service.summarize_chapter(req.text, language=req.language or "en")
    return schemas.SummarizeResponse(summary=summary, chapter_id=req.chapter_id)


@app.post(
    "/api/ai/translate",
    response_model=schemas.TranslateResponse,
    tags=["AI Services"],
)
def translate_endpoint(
    req: schemas.TranslateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Translate text between English, Tamil, and Sinhala using Gemini AI."""
    translated = gemini_service.translate_text(
        req.text,
        source_lang=req.source_language or "en",
        target_lang=req.target_language,
    )

    if req.chapter_id:
        chap = db.query(models.Chapter).filter(models.Chapter.id == req.chapter_id).first()
        if chap:
            chap.processed_text = translated
            db.commit()

    return schemas.TranslateResponse(
        translated_text=translated,
        source_language=req.source_language or "en",
        target_language=req.target_language,
        chapter_id=req.chapter_id,
    )


# ==========================================
# TEXT-TO-SPEECH (TTS) & AUDIO ENDPOINTS
# ==========================================

# Concurrency tracker for background audiobook chapter generation
generation_jobs_lock = threading.Lock()
# Structure: { document_id: { chapter_id: {"status": "pending"|"processing"|"completed"|"failed", "error": None} } }
active_chapter_status: Dict[int, Dict[int, Dict[str, Any]]] = {}
# Dynamic priority boost queue for user-selected chapters: { document_id: [chapter_id, ...] }
chapter_priority_boosts: Dict[int, List[int]] = {}


def process_audiobook_background_task(
    document_id: int,
    job_id: int,
    voice_name: Optional[str] = None,
    language: Optional[str] = None,
    force_regenerate: bool = False,
):
    """
    Background worker for audiobook synthesis:
    1. Chapter 1 Priority: Immediately synthesizes Chapter 1 so playback is ready without waiting.
    2. Dynamic User Priority: Synthesizes user-selected boosted chapters first.
    3. Controlled Concurrency: Synthesizes remaining chapters using a thread pool with max 2 workers.
    4. Live Progress: Updates in-memory tracker and commits completed audio to database as each finishes.
    """
    db = SessionLocal()
    try:
        doc = db.query(models.Document).filter(models.Document.id == document_id).first()
        if not doc:
            return

        chapters = (
            db.query(models.Chapter)
            .filter(models.Chapter.document_id == document_id)
            .order_by(models.Chapter.chapter_number.asc())
            .all()
        )
        if not chapters:
            return

        target_lang = language or doc.source_language or "en"

        # Initialize progress tracking state
        with generation_jobs_lock:
            if document_id not in active_chapter_status:
                active_chapter_status[document_id] = {}
            for chap in chapters:
                if chap.audio_file_url and not force_regenerate:
                    active_chapter_status[document_id][chap.id] = {
                        "status": "completed",
                        "error": None,
                    }
                else:
                    active_chapter_status[document_id][chap.id] = {
                        "status": "pending",
                        "error": None,
                    }

        # -------------------------------------------------------------
        # 1. PRIORITY GENERATION: CHAPTER 1 FIRST
        # -------------------------------------------------------------
        first_chap = chapters[0]
        if force_regenerate or not first_chap.audio_file_url:
            with generation_jobs_lock:
                active_chapter_status[document_id][first_chap.id]["status"] = "processing"

            try:
                first_text = first_chap.processed_text or first_chap.original_text or ""
                if first_text.strip():
                    tts_res = tts_service.generate_speech(
                        text=first_text,
                        language=target_lang,
                        voice_name=voice_name,
                        force_regenerate=force_regenerate,
                    )
                    first_chap.audio_file_url = tts_res["audio_url"]
                    first_chap.duration_seconds = tts_res["duration_seconds"]
                    db.commit()
                    db.refresh(first_chap)

                    with generation_jobs_lock:
                        active_chapter_status[document_id][first_chap.id]["status"] = "completed"
                        active_chapter_status[document_id][first_chap.id]["error"] = None
                    logger.info(f"[Priority] Chapter 1 of doc {document_id} synthesized successfully! Audio ready for playback.")
            except Exception as e:
                logger.error(f"[Priority] Failed to synthesize Chapter 1: {e}")
                with generation_jobs_lock:
                    active_chapter_status[document_id][first_chap.id]["status"] = "failed"
                    active_chapter_status[document_id][first_chap.id]["error"] = str(e)

        # -------------------------------------------------------------
        # 2. CONTROLLED PARALLEL WORKER FOR REMAINING CHAPTERS (MAX 2 WORKERS)
        # Dynamic priority: boosted chapters are processed first
        # -------------------------------------------------------------
        boosts = chapter_priority_boosts.get(document_id, [])
        remaining_chapters = sorted(
            [c for c in chapters[1:] if force_regenerate or not c.audio_file_url],
            key=lambda ch: (0 if ch.id in boosts else 1, ch.chapter_number),
        )

        def synthesize_single_chapter(chap_id: int, chap_text: str):
            thread_db = SessionLocal()
            try:
                with generation_jobs_lock:
                    active_chapter_status[document_id][chap_id]["status"] = "processing"

                tts_res = tts_service.generate_speech(
                    text=chap_text,
                    language=target_lang,
                    voice_name=voice_name,
                    force_regenerate=force_regenerate,
                )

                chap_rec = thread_db.query(models.Chapter).filter(models.Chapter.id == chap_id).first()
                if chap_rec:
                    chap_rec.audio_file_url = tts_res["audio_url"]
                    chap_rec.duration_seconds = tts_res["duration_seconds"]
                    thread_db.commit()

                with generation_jobs_lock:
                    active_chapter_status[document_id][chap_id]["status"] = "completed"
                    active_chapter_status[document_id][chap_id]["error"] = None
                logger.info(f"Chapter #{chap_id} synthesized successfully.")
            except Exception as chap_err:
                logger.error(f"Error synthesizing chapter #{chap_id}: {chap_err}")
                with generation_jobs_lock:
                    active_chapter_status[document_id][chap_id]["status"] = "failed"
                    active_chapter_status[document_id][chap_id]["error"] = str(chap_err)
            finally:
                thread_db.close()

        if remaining_chapters:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(
                        synthesize_single_chapter,
                        c.id,
                        c.processed_text or c.original_text or "",
                    )
                    for c in remaining_chapters
                ]
                concurrent.futures.wait(futures)

        # Mark ProcessingJob as completed
        job = db.query(models.ProcessingJob).filter(models.ProcessingJob.id == job_id).first()
        if job:
            job.status = models.JobStatus.COMPLETED
            db.commit()


    except Exception as overall_err:
        logger.error(f"Background audiobook generation error for doc {document_id}: {overall_err}")
        try:
            job = db.query(models.ProcessingJob).filter(models.ProcessingJob.id == job_id).first()
            if job:
                job.status = models.JobStatus.FAILED
                job.error_message = str(overall_err)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@app.get(
    "/api/tts/voices",
    response_model=schemas.AvailableVoicesResponse,
    tags=["Audio & TTS"],
)
def get_available_voices_endpoint(language: Optional[str] = "en"):
    """Retrieve available TTS voices for a selected language (Azure / Gemini / Google)."""
    voices = tts_service.get_available_voices(language or "en")
    return schemas.AvailableVoicesResponse(
        provider=tts_service.TTS_PROVIDER,
        language=language or "en",
        voices=[schemas.VoiceItem(**v) for v in voices],
    )


@app.post(
    "/api/documents/{document_id}/generate-audio",
    response_model=schemas.GenerateAudiobookResponse,
    tags=["Audio & TTS"],
)
def generate_full_audiobook_endpoint(
    document_id: int,
    req: schemas.GenerateAudiobookRequest,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initiate background audiobook generation with Chapter 1 Priority and Azure TTS.
    Returns immediately with a job ID so the frontend can display live chapter progress.
    """
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.user_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    chapters = (
        db.query(models.Chapter)
        .filter(models.Chapter.document_id == document_id)
        .order_by(models.Chapter.chapter_number.asc())
        .all()
    )
    if not chapters:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no chapters. Please extract and detect chapters first.",
        )

    # Create processing job record
    job = models.ProcessingJob(
        document_id=doc.id,
        job_type="audiobook_generation",
        status=models.JobStatus.PROCESSING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch background priority task
    background_tasks.add_task(
        process_audiobook_background_task,
        doc.id,
        job.id,
        voice_name=req.voice_name,
        language=req.language or doc.source_language,
        force_regenerate=req.force_regenerate or False,
    )

    return schemas.GenerateAudiobookResponse(
        job_id=job.id,
        document_id=doc.id,
        status="processing",
        message="Audiobook generation started. Chapter 1 is prioritized for immediate playback.",
        provider=tts_service.TTS_PROVIDER,
    )


@app.get(
    "/api/documents/{document_id}/audio-progress",
    response_model=schemas.AudiobookProgressResponse,
    tags=["Audio & TTS"],
)
def get_audiobook_progress_endpoint(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve chapter-level generation progress and status for an audiobook."""
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.user_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    chapters = (
        db.query(models.Chapter)
        .filter(models.Chapter.document_id == document_id)
        .order_by(models.Chapter.chapter_number.asc())
        .all()
    )

    doc_tracker = active_chapter_status.get(document_id, {})
    total_chapters = len(chapters)
    completed_count = 0
    chapter_items = []
    has_processing = False
    has_failed = False

    for c in chapters:
        c_status = "pending"
        c_error = None

        if c.id in doc_tracker:
            c_status = doc_tracker[c.id]["status"]
            c_error = doc_tracker[c.id].get("error")

        if c.audio_file_url:
            c_status = "completed"
            completed_count += 1
        elif c_status == "processing":
            has_processing = True
        elif c_status == "failed":
            has_failed = True

        chapter_items.append(
            schemas.AudiobookChapterProgress(
                chapter_id=c.id,
                chapter_number=c.chapter_number,
                title=c.title or f"Chapter {c.chapter_number}",
                status=c_status,
                audio_url=c.audio_file_url,
                duration_seconds=c.duration_seconds or 0.0,
                error=c_error,
            )
        )

    overall_percent = int((completed_count / total_chapters) * 100) if total_chapters > 0 else 0
    overall_status = "completed" if completed_count == total_chapters and total_chapters > 0 else (
        "processing" if has_processing else ("failed" if has_failed and completed_count == 0 else "idle")
    )

    return schemas.AudiobookProgressResponse(
        document_id=doc.id,
        total_chapters=total_chapters,
        completed_chapters=completed_count,
        overall_progress_percent=overall_percent,
        status=overall_status,
        provider=tts_service.TTS_PROVIDER,
        chapters=chapter_items,
    )


@app.post(
    "/api/chapters/{chapter_id}/retry-audio",
    response_model=schemas.TTSGenerateResponse,
    tags=["Audio & TTS"],
)
def retry_chapter_audio_endpoint(
    chapter_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retry audio generation specifically for a single failed chapter."""
    chap = db.query(models.Chapter).filter(models.Chapter.id == chapter_id).first()
    if not chap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    doc = db.query(models.Document).filter(models.Document.id == chap.document_id).first()
    if doc and doc.user_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    text_to_narrate = chap.processed_text or chap.original_text
    if not text_to_narrate or not text_to_narrate.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No chapter text available.")

    target_lang = doc.source_language if doc else "en"

    # Set status to processing
    if doc:
        with generation_jobs_lock:
            if doc.id in active_chapter_status:
                active_chapter_status[doc.id][chap.id] = {"status": "processing", "error": None}

    try:
        tts_res = tts_service.generate_speech(
            text=text_to_narrate,
            language=target_lang,
            force_regenerate=True,
        )
        chap.audio_file_url = tts_res["audio_url"]
        chap.duration_seconds = tts_res["duration_seconds"]
        db.commit()
        db.refresh(chap)

        if doc:
            with generation_jobs_lock:
                if doc.id in active_chapter_status:
                    active_chapter_status[doc.id][chap.id] = {"status": "completed", "error": None}

        return schemas.TTSGenerateResponse(
            chapter_id=chap.id,
            audio_url=chap.audio_file_url,
            duration_seconds=chap.duration_seconds,
            format=tts_res["format"],
            language=tts_res["language"],
            provider=tts_res["provider"],
        )
    except Exception as exc:
        if doc:
            with generation_jobs_lock:
                if doc.id in active_chapter_status:
                    active_chapter_status[doc.id][chap.id] = {"status": "failed", "error": str(exc)}
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.post(
    "/api/tts/generate",
    response_model=schemas.TTSGenerateResponse,
    tags=["Audio & TTS"],
)
def generate_audio_endpoint(
    req: schemas.TTSGenerateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate TTS audio for a single chapter using Primary Azure TTS (or fallbacks).
    Saves audio file locally, stores metadata & audio URL in MySQL Chapter row.
    """
    chap = db.query(models.Chapter).filter(models.Chapter.id == req.chapter_id).first()
    if not chap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    text_to_narrate = req.text or chap.processed_text or chap.original_text
    if not text_to_narrate or not text_to_narrate.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No text available to narrate.")

    try:
        tts_res = tts_service.generate_speech(
            text=text_to_narrate,
            language=req.language or "en",
            voice_name=req.voice_name,
        )

        # Update Chapter record with audio URL and duration
        chap.audio_file_url = tts_res["audio_url"]
        chap.duration_seconds = tts_res["duration_seconds"]
        db.commit()
        db.refresh(chap)

        return schemas.TTSGenerateResponse(
            chapter_id=chap.id,
            audio_url=chap.audio_file_url,
            duration_seconds=chap.duration_seconds,
            format=tts_res["format"],
            language=tts_res["language"],
            provider=tts_res["provider"],
        )
    except Exception as exc:
        logger.error(f"Audio generation failed for chapter #{chap.id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio generation failed: {str(exc)}",
        )



@app.get("/api/audio/{filename}", tags=["Audio & TTS"])
def stream_audio(filename: str):
    """Serve or stream generated audio file."""
    filepath = get_audio_filepath(filename)
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found")

    ext = filepath.suffix.lower()
    media_type = "audio/wav" if ext == ".wav" else "audio/mpeg"
    return FileResponse(filepath, media_type=media_type, filename=filename)


@app.post(
    "/api/chapters/{chapter_id}/prioritize",
    tags=["Audio & TTS"],
)
def prioritize_chapter_endpoint(
    chapter_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dynamically boost a user-selected chapter to the front of the generation queue."""
    chap = db.query(models.Chapter).filter(models.Chapter.id == chapter_id).first()
    if not chap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    with generation_jobs_lock:
        if chap.document_id not in chapter_priority_boosts:
            chapter_priority_boosts[chap.document_id] = []
        if chapter_id not in chapter_priority_boosts[chap.document_id]:
            chapter_priority_boosts[chap.document_id].insert(0, chapter_id)

    return {"message": f"Chapter #{chap.chapter_number} prioritized for synthesis."}


@app.get(
    "/api/chapters/{chapter_id}/stream",
    tags=["Audio & TTS"],
)
def stream_chapter_audio_endpoint(
    chapter_id: int,
    db: Session = Depends(get_db),
):
    """
    Stream audio in real-time chunks for instant playback without waiting for full chapter completion.
    If cached audio already exists, serves directly; otherwise streams live from TTS provider.
    """
    chap = db.query(models.Chapter).filter(models.Chapter.id == chapter_id).first()
    if not chap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

    doc = db.query(models.Document).filter(models.Document.id == chap.document_id).first()
    lang = doc.source_language if doc else "en"

    # If file is already generated and present on disk, stream directly
    if chap.audio_file_url:
        filename = Path(chap.audio_file_url).name
        filepath = get_audio_filepath(filename)
        if filepath.exists() and filepath.is_file():
            media_type = "audio/wav" if filepath.suffix.lower() == ".wav" else "audio/mpeg"
            return FileResponse(filepath, media_type=media_type, filename=filename)

    text_to_narrate = chap.processed_text or chap.original_text
    if not text_to_narrate or not text_to_narrate.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No chapter text available.")

    def audio_stream_generator():
        accumulated_bytes = bytearray()
        try:
            for chunk in tts_service.stream_speech_chunks(text_to_narrate, language=lang):
                accumulated_bytes.extend(chunk)
                yield chunk
        finally:
            if accumulated_bytes:
                # Save complete file to cache and update chapter record asynchronously
                def save_cached_audio():
                    thread_db = SessionLocal()
                    try:
                        tts_res = tts_service.generate_speech(text_to_narrate, language=lang)
                        rec = thread_db.query(models.Chapter).filter(models.Chapter.id == chapter_id).first()
                        if rec:
                            rec.audio_file_url = tts_res["audio_url"]
                            rec.duration_seconds = tts_res["duration_seconds"]
                            thread_db.commit()
                    except Exception as e:
                        logger.warning(f"Error persisting streamed audio for chapter {chapter_id}: {e}")
                    finally:
                        thread_db.close()
                threading.Thread(target=save_cached_audio, daemon=True).start()

    return StreamingResponse(
        audio_stream_generator(),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": f"inline; filename=chapter_{chap.chapter_number}.mp3",
        },
    )

