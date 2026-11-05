import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator


# ============================================================================
# User Schemas
# ============================================================================

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


# ============================================================================
# Token Schemas
# ============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


# ============================================================================
# Chapter & Document Schemas (Member 3 - Document Processing & Dashboard)
# ============================================================================

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


class DocumentListItem(BaseModel):
    id: int
    user_id: int
    title: str
    file_type: str
    source_file_url: str
    mode: str
    source_language: str
    target_language: Optional[str] = None
    created_at: datetime
    chapter_count: int = 0
    status: str = "completed"
    total_characters: int = 0
    has_audio: bool = False

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(BaseModel):
    id: int
    user_id: int
    title: str
    file_type: str
    source_file_url: str
    mode: str
    source_language: str
    target_language: Optional[str] = None
    created_at: datetime
    status: str = "completed"
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    chapters: List[ChapterResponse] = Field(default_factory=list)
    total_characters: int = 0
    total_words: int = 0
    raw_text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardStatsResponse(BaseModel):
    total_documents: int
    processed_documents: int
    processing_documents: int
    audiobooks_generated: int
    recent_documents: List[DocumentListItem] = Field(default_factory=list)
    recent_activities: List[Dict[str, Any]] = Field(default_factory=list)
