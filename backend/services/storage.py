import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException, status

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
DOCUMENTS_DIR = UPLOAD_DIR / "documents"
AUDIO_DIR = UPLOAD_DIR / "audio"

# Ensure upload directories exist
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


def validate_file(file: UploadFile) -> str:
    """Validate file extension and return normalized extension."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    return ext


async def save_uploaded_file(file: UploadFile) -> tuple[str, str, int]:
    """
    Save uploaded file into DOCUMENTS_DIR with a unique filename.
    Returns: (stored_filename, absolute_path, file_size_bytes)
    """
    ext = validate_file(file)
    safe_basename = Path(file.filename).stem[:40].replace(" ", "_")
    unique_filename = f"{uuid.uuid4().hex[:12]}_{safe_basename}{ext}"
    destination_path = DOCUMENTS_DIR / unique_filename

    total_bytes = 0
    try:
        async with aiofiles.open(destination_path, "wb") as out_file:
            while chunk := await file.read(1024 * 64):  # 64 KB chunks
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE_BYTES:
                    # Clean up file and abort
                    await out_file.close()
                    if destination_path.exists():
                        destination_path.unlink()
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File exceeds maximum size limit of 50 MB",
                    )
                await out_file.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        if destination_path.exists():
            destination_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(exc)}",
        )

    return unique_filename, str(destination_path), total_bytes


def get_audio_filepath(filename: str) -> Path:
    """Get absolute path to an audio file inside AUDIO_DIR."""
    return AUDIO_DIR / filename

