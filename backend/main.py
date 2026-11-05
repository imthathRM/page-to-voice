from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import engine, Base, get_db
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth")


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
    version="1.1.0",
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
    # Check if email is already registered
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    # Check if username is already taken
    if db.query(models.User).filter(models.User.username == user_in.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken",
        )

    # Create new user with bcrypt hash (cost 12)
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
    Hardened authentication endpoint:
    - Brute-force & rate-limiting protection per identifier and IP
    - Constant-time verification to prevent user enumeration (timing attacks)
    - Support for login by username OR email
    - Comprehensive security audit logging
    """
    client_ip = get_client_ip(request)
    identifier = (credentials.email or credentials.username or "").strip().lower()
    ip_key = f"ip:{client_ip}"
    user_key = f"user:{identifier}"

    # 1. Check Rate Limiting / Lockout Status
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

    # 2. Query user by email OR username
    user = (
        db.query(models.User)
        .filter(
            (models.User.email == identifier)
            | (models.User.username == identifier)
        )
        .first()
    )

    # 3. Constant-time verification & validation
    if not user:
        # Mitigate timing attack by hashing dummy password
        verify_dummy_password(credentials.password)
        login_rate_limiter.record_failure(ip_key)
        login_rate_limiter.record_failure(user_key)
        logger.warning(f"Failed login (user not found) for identifier: {identifier} from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(credentials.password, user.password_hash):
        login_rate_limiter.record_failure(ip_key)
        login_rate_limiter.record_failure(user_key)
        logger.warning(f"Failed login (invalid password) for user_id={user.id} from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Check account status
    if not user.is_active:
        logger.warning(f"Login attempted on inactive account user_id={user.id} from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended",
        )

    # 5. Successful login: reset failure counters
    login_rate_limiter.record_success(ip_key)
    login_rate_limiter.record_success(user_key)
    logger.info(f"Successful login for user_id={user.id} ({user.email}) from IP: {client_ip}")

    # 6. Issue hardened JWT token
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


# ============================================================================
# Document Processing & Management Endpoints (Member 3)
# ============================================================================

from datetime import datetime
import os
import shutil
from typing import Any, Dict, List, Optional
import uuid
from pathlib import Path
from fastapi import File, Form, UploadFile
from sqlalchemy import desc, func
from document_processing import (
    parse_document,
    get_supported_formats,
    DocumentProcessingError,
    CorruptedDocumentException,
    UnsupportedFileFormatException,
)

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB


@app.post(
    "/documents/upload",
    response_model=schemas.DocumentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
)
def upload_and_process_document(
    file: UploadFile = File(...),
    mode: str = Form("document"),
    source_language: str = Form("en"),
    target_language: Optional[str] = Form(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a document and trigger parsing extraction.
    Supports PDF, DOCX, TXT, PPTX, EPUB, RTF formats.
    Extracts structured chapters/sections and returns extraction result.
    """
    filename = file.filename or "uploaded_document"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    supported_exts = get_supported_formats()
    if ext not in supported_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Supported formats: {', '.join(supported_exts)}",
        )

    # Prepare secure user upload directory
    user_upload_dir = UPLOAD_DIR / str(current_user.id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    unique_prefix = uuid.uuid4().hex[:12]
    safe_name = f"{unique_prefix}_{Path(filename).name}"
    saved_path = user_upload_dir / safe_name

    # Save uploaded file while monitoring byte count
    total_bytes = 0
    try:
        with open(saved_path, "wb") as buffer:
            reader = file.file if hasattr(file, "file") else file
            while chunk := reader.read(1024 * 64):
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File size exceeds the 25MB limit.",
                    )
                buffer.write(chunk)
    except HTTPException:
        if saved_path.exists():
            saved_path.unlink()
        raise
    except Exception as e:
        if saved_path.exists():
            saved_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}",
        )

    # 1. Create Document database record
    mode_str = mode if isinstance(mode, str) else "document"
    source_lang_str = source_language if isinstance(source_language, str) else "en"
    target_lang_str = target_language if isinstance(target_language, str) else None

    mode_enum = models.DocumentMode.BOOK if mode_str.lower() == "book" else models.DocumentMode.DOCUMENT
    doc_record = models.Document(
        user_id=current_user.id,
        title=filename.rsplit(".", 1)[0].replace("_", " ").title(),
        file_type=ext,
        source_file_url=str(saved_path.as_posix()),
        mode=mode_enum,
        source_language=source_lang_str,
        target_language=target_lang_str,
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # 2. Create ProcessingJob record
    job_record = models.ProcessingJob(
        document_id=doc_record.id,
        job_type="text_extraction",
        status=models.JobStatus.PROCESSING,
    )
    db.add(job_record)
    db.commit()

    # 3. Perform text extraction using Document Processing Engine
    warnings: List[str] = []
    extraction_status = "completed"
    error_msg: Optional[str] = None
    created_chapters: List[models.Chapter] = []

    try:
        result = parse_document(saved_path)
        warnings.extend(result.warnings)

        if result.is_success or result.sections:
            # Populate chapter / section entities
            if result.sections:
                for sec in result.sections:
                    chap = models.Chapter(
                        document_id=doc_record.id,
                        chapter_number=sec.index,
                        title=sec.title or f"{sec.section_type.capitalize()} {sec.index}",
                        original_text=sec.content,
                        processed_text=sec.content,
                        duration_seconds=0.0,
                    )
                    db.add(chap)
                    created_chapters.append(chap)
            else:
                # Document has text without explicit section divisions
                single_chap = models.Chapter(
                    document_id=doc_record.id,
                    chapter_number=1,
                    title="Main Content",
                    original_text=result.text,
                    processed_text=result.text,
                    duration_seconds=0.0,
                )
                db.add(single_chap)
                created_chapters.append(single_chap)

            job_record.status = models.JobStatus.COMPLETED
            db.commit()
            for c in created_chapters:
                db.refresh(c)

        else:
            extraction_status = "failed"
            error_msg = result.error or "Document extraction returned empty content."
            job_record.status = models.JobStatus.FAILED
            job_record.error_message = error_msg
            db.commit()

    except CorruptedDocumentException as cde:
        extraction_status = "failed"
        error_msg = f"Corrupted or invalid document: {str(cde)}"
        job_record.status = models.JobStatus.FAILED
        job_record.error_message = error_msg
        db.commit()

    except Exception as exc:
        extraction_status = "failed"
        error_msg = f"Processing error: {str(exc)}"
        job_record.status = models.JobStatus.FAILED
        job_record.error_message = error_msg
        db.commit()

    # Construct and return full response
    all_text = "\n\n".join(c.original_text or "" for c in created_chapters)
    return schemas.DocumentDetailResponse(
        id=doc_record.id,
        user_id=doc_record.user_id,
        title=doc_record.title,
        file_type=doc_record.file_type,
        source_file_url=doc_record.source_file_url,
        mode=doc_record.mode.value if hasattr(doc_record.mode, "value") else str(doc_record.mode),
        source_language=doc_record.source_language,
        target_language=doc_record.target_language,
        created_at=doc_record.created_at,
        status=extraction_status,
        error_message=error_msg,
        warnings=warnings,
        chapters=[schemas.ChapterResponse.model_validate(c) for c in created_chapters],
        total_characters=len(all_text),
        total_words=len(all_text.split()) if all_text else 0,
        raw_text=all_text,
    )


@app.get(
    "/documents",
    response_model=List[schemas.DocumentListItem],
    tags=["Documents"],
)
def list_user_documents(
    search: Optional[str] = None,
    file_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all documents belonging to the authenticated user.
    Supports filtering by search query, file format, and processing status.
    """
    query = db.query(models.Document).filter(models.Document.user_id == current_user.id)

    if file_type and file_type.lower() != "all":
        query = query.filter(models.Document.file_type == file_type.lower())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(models.Document.title.ilike(term))

    docs = query.order_by(desc(models.Document.created_at)).all()

    items: List[schemas.DocumentListItem] = []
    for d in docs:
        chap_count = len(d.chapters)
        has_audio = any(c.audio_file_url is not None for c in d.chapters)

        # Determine status from processing_jobs or chapter existence
        doc_status = "completed"
        if d.processing_jobs:
            latest_job = max(d.processing_jobs, key=lambda j: j.created_at or datetime.min)
            status_val = latest_job.status.value if hasattr(latest_job.status, "value") else str(latest_job.status)
            doc_status = status_val
        elif chap_count == 0:
            doc_status = "processing"

        if status_filter and status_filter.lower() != "all" and doc_status != status_filter.lower():
            continue

        total_chars = sum(len(c.original_text or "") for c in d.chapters)
        mode_str = d.mode.value if hasattr(d.mode, "value") else str(d.mode)

        items.append(
            schemas.DocumentListItem(
                id=d.id,
                user_id=d.user_id,
                title=d.title,
                file_type=d.file_type,
                source_file_url=d.source_file_url,
                mode=mode_str,
                source_language=d.source_language,
                target_language=d.target_language,
                created_at=d.created_at,
                chapter_count=chap_count,
                status=doc_status,
                total_characters=total_chars,
                has_audio=has_audio,
            )
        )

    return items


@app.get(
    "/documents/{document_id}",
    response_model=schemas.DocumentDetailResponse,
    tags=["Documents"],
)
def get_document_details(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve full details, extracted text, and chapters for a specific document.
    Enforces user ownership security.
    """
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    # Secure document ownership check
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if doc.user_id != current_user.id and role_val != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this document.",
        )

    sorted_chapters = sorted(doc.chapters, key=lambda c: c.chapter_number)
    all_text = "\n\n".join(c.original_text or "" for c in sorted_chapters)

    doc_status = "completed"
    error_msg = None
    if doc.processing_jobs:
        latest_job = max(doc.processing_jobs, key=lambda j: j.created_at or datetime.min)
        doc_status = latest_job.status.value if hasattr(latest_job.status, "value") else str(latest_job.status)
        error_msg = latest_job.error_message
    elif len(sorted_chapters) == 0:
        doc_status = "processing"

    mode_str = doc.mode.value if hasattr(doc.mode, "value") else str(doc.mode)

    return schemas.DocumentDetailResponse(
        id=doc.id,
        user_id=doc.user_id,
        title=doc.title,
        file_type=doc.file_type,
        source_file_url=doc.source_file_url,
        mode=mode_str,
        source_language=doc.source_language,
        target_language=doc.target_language,
        created_at=doc.created_at,
        status=doc_status,
        error_message=error_msg,
        warnings=[],
        chapters=[schemas.ChapterResponse.model_validate(c) for c in sorted_chapters],
        total_characters=len(all_text),
        total_words=len(all_text.split()) if all_text else 0,
        raw_text=all_text,
    )


@app.delete(
    "/documents/{document_id}",
    tags=["Documents"],
)
def delete_document(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a document, its associated chapters, and local source file.
    Enforces user ownership security.
    """
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if doc.user_id != current_user.id and role_val != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this document.",
        )

    # Clean up local file if present
    if doc.source_file_url and Path(doc.source_file_url).exists():
        try:
            Path(doc.source_file_url).unlink()
        except OSError:
            pass

    db.delete(doc)
    db.commit()
    return {"status": "success", "message": f"Document '{doc.title}' deleted successfully."}


@app.get(
    "/dashboard/stats",
    response_model=schemas.DashboardStatsResponse,
    tags=["Dashboard"],
)
def get_dashboard_statistics(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve aggregated dashboard statistics and recent activities for authenticated user.
    """
    docs = (
        db.query(models.Document)
        .filter(models.Document.user_id == current_user.id)
        .order_by(desc(models.Document.created_at))
        .all()
    )

    total_docs = len(docs)
    processed_count = 0
    processing_count = 0
    audiobooks_count = 0
    recent_items: List[schemas.DocumentListItem] = []
    activities: List[Dict[str, Any]] = []

    for idx, d in enumerate(docs):
        chap_count = len(d.chapters)
        has_audio = any(c.audio_file_url is not None for c in d.chapters)
        if has_audio:
            audiobooks_count += 1

        doc_status = "completed"
        if d.processing_jobs:
            latest_job = max(d.processing_jobs, key=lambda j: j.created_at or datetime.min)
            doc_status = latest_job.status.value if hasattr(latest_job.status, "value") else str(latest_job.status)
        elif chap_count == 0:
            doc_status = "processing"

        if doc_status == "completed":
            processed_count += 1
        elif doc_status == "processing":
            processing_count += 1

        total_chars = sum(len(c.original_text or "") for c in d.chapters)
        mode_str = d.mode.value if hasattr(d.mode, "value") else str(d.mode)

        item = schemas.DocumentListItem(
            id=d.id,
            user_id=d.user_id,
            title=d.title,
            file_type=d.file_type,
            source_file_url=d.source_file_url,
            mode=mode_str,
            source_language=d.source_language,
            target_language=d.target_language,
            created_at=d.created_at,
            chapter_count=chap_count,
            status=doc_status,
            total_characters=total_chars,
            has_audio=has_audio,
        )

        if idx < 5:
            recent_items.append(item)
            activities.append({
                "id": f"act_{d.id}",
                "type": "upload",
                "title": f"Uploaded {d.title}",
                "description": f"Format: {d.file_type.upper()} • {chap_count} section(s)",
                "timestamp": d.created_at.isoformat() if d.created_at else datetime.utcnow().isoformat(),
                "status": doc_status,
            })

    return schemas.DashboardStatsResponse(
        total_documents=total_docs,
        processed_documents=processed_count,
        processing_documents=processing_count,
        audiobooks_generated=audiobooks_count,
        recent_documents=recent_items,
        recent_activities=activities,
    )
