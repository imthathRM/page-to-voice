import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    Text,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    func,
)
from sqlalchemy.orm import relationship
from database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class DocumentMode(str, enum.Enum):
    BOOK = "book"
    DOCUMENT = "document"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        SAEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.USER,
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    documents = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    listening_progress = relationship(
        "ListeningProgress",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    source_file_url = Column(String(1024), nullable=False)
    mode = Column(
        SAEnum(DocumentMode, values_callable=lambda x: [e.value for e in x]),
        default=DocumentMode.DOCUMENT,
        nullable=False,
    )
    source_language = Column(String(20), default="en", nullable=False)
    target_language = Column(String(20), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="documents")
    chapters = relationship(
        "Chapter",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    listening_progress = relationship(
        "ListeningProgress",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    processing_jobs = relationship(
        "ProcessingJob",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    original_text = Column(Text, nullable=True)
    processed_text = Column(Text, nullable=True)
    audio_file_url = Column(String(1024), nullable=True)
    duration_seconds = Column(Float, default=0.0, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    document = relationship("Document", back_populates="chapters")
    listening_progress = relationship(
        "ListeningProgress",
        back_populates="last_chapter",
    )


class ListeningProgress(Base):
    __tablename__ = "listening_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    last_chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    current_position_seconds = Column(Float, default=0.0, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="listening_progress")
    document = relationship("Document", back_populates="listening_progress")
    last_chapter = relationship("Chapter", back_populates="listening_progress")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_type = Column(String(100), nullable=False)
    status = Column(
        SAEnum(JobStatus, values_callable=lambda x: [e.value for e in x]),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
    )
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    document = relationship("Document", back_populates="processing_jobs")
