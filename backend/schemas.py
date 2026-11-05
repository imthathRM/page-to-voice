import re
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        trimmed = v.strip()
        if not re.match(r"^[a-zA-Z0-9_-]+$", trimmed):
            raise ValueError("Username can only contain alphanumeric characters, underscores, and hyphens.")
        return trimmed


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            raise ValueError("Password must contain at least one special character.")
        if " " in v:
            raise ValueError("Password must not contain spaces.")
        return v


class UserLogin(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_identifier(self):
        if not self.email and not self.username:
            raise ValueError("Either email or username must be provided to log in.")
        return self


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


# Document & Chapter Schemas
class ChapterResponse(BaseModel):
    id: int
    document_id: int
    chapter_number: int
    title: Optional[str] = None
    original_text: Optional[str] = None
    processed_text: Optional[str] = None
    audio_file_url: Optional[str] = None
    duration_seconds: Optional[float] = 0.0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: int
    user_id: int
    title: str
    file_type: str
    source_file_url: str
    mode: str
    source_language: str
    target_language: Optional[str] = None
    status: Optional[str] = "uploaded"
    created_at: datetime
    chapter_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    chapters: List[ChapterResponse] = []
    error_message: Optional[str] = None


class DocumentProcessResponse(BaseModel):
    document_id: int
    status: str
    message: str
    detected_language: str
    chapter_count: int


# AI Request/Response Schemas
class CleanTextRequest(BaseModel):
    text: str
    language: Optional[str] = "en"
    chapter_id: Optional[int] = None


class CleanTextResponse(BaseModel):
    cleaned_text: str
    chapter_id: Optional[int] = None


class SummarizeRequest(BaseModel):
    text: str
    language: Optional[str] = "en"
    chapter_id: Optional[int] = None


class SummarizeResponse(BaseModel):
    summary: str
    chapter_id: Optional[int] = None


class TranslateRequest(BaseModel):
    text: str
    source_language: Optional[str] = "en"
    target_language: str = Field(..., description="Target language: en, ta, or si")
    chapter_id: Optional[int] = None


class TranslateResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    chapter_id: Optional[int] = None


class TTSGenerateRequest(BaseModel):
    chapter_id: int
    text: Optional[str] = None
    language: Optional[str] = "en"
    voice_name: Optional[str] = None


class TTSGenerateResponse(BaseModel):
    chapter_id: int
    audio_url: str
    duration_seconds: float
    format: str
    language: str
    provider: str


# Batch Audiobook Generation Schemas
class AudiobookChapterProgress(BaseModel):
    chapter_id: int
    chapter_number: int
    title: Optional[str] = None
    status: str  # pending, processing, completed, failed
    audio_url: Optional[str] = None
    duration_seconds: Optional[float] = 0.0
    error: Optional[str] = None


class AudiobookProgressResponse(BaseModel):
    document_id: int
    total_chapters: int
    completed_chapters: int
    overall_progress_percent: int
    status: str  # pending, processing, completed, failed
    provider: str
    chapters: List[AudiobookChapterProgress] = []


class GenerateAudiobookRequest(BaseModel):
    voice_name: Optional[str] = None
    language: Optional[str] = None
    force_regenerate: Optional[bool] = False


class GenerateAudiobookResponse(BaseModel):
    job_id: int
    document_id: int
    status: str
    message: str
    provider: str


class VoiceItem(BaseModel):
    name: str
    gender: str
    label: str
    locale: Optional[str] = None


class AvailableVoicesResponse(BaseModel):
    provider: str
    language: str
    voices: List[VoiceItem]

