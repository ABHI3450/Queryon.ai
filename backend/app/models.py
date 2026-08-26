"""
SQLAlchemy Database Configuration & Models
===========================================
Defines the database tables for Users, Uploads, Reports, and Jobs.

WHY THESE MODELS:
- `users`: Synced from Clerk webhook; tracks monthly usage for tier limits (10/month)
- `uploads`: Stores file metadata (original filename, S3/local storage key, file size, row/col count)
- `jobs`: Stores asynchronous job progress state and status tracking (pending/cleaning/analyzing/visualizing/explaining/completed/failed)
- `reports`: Stores generated output (cleaning summary JSON, findings JSON, chart paths JSON, markdown report)
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any

from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, Enum, Index, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import settings

# Create Async Engine — supports both PostgreSQL (production) and SQLite (local dev)
db_url = settings.database_url
_is_sqlite = "sqlite" in db_url

if _is_sqlite:
    if not db_url.startswith("sqlite+aiosqlite"):
        db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    engine = create_async_engine(
        db_url,
        echo=settings.debug,
        future=True,
    )
else:
    engine = create_async_engine(
        db_url,
        echo=settings.debug,
        future=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,  # Recycle connections every 30 minutes
        pool_pre_ping=True,  # Verify connection health before use
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    """Base declarative class for all models."""
    pass

async def get_db():
    """Dependency for delivering async DB sessions in FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class JobStatusEnum(str, enum.Enum):
    PENDING = "pending"
    CLEANING = "cleaning"
    ANALYZING = "analyzing"
    VISUALIZING = "visualizing"
    EXPLAINING = "explaining"
    COMPLETED = "completed"
    FAILED = "failed"

class UserTierEnum(str, enum.Enum):
    FREE = "free"
    PRO = "pro"

# ─────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────

class UserModel(Base):
    __tablename__ = "users"

    # Store Clerk User ID directly (e.g. "user_2bX...")
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    tier: Mapped[str] = mapped_column(String(50), default=UserTierEnum.FREE.value, nullable=False)
    monthly_usage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usage_reset_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    uploads: Mapped[List["UploadModel"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reports: Mapped[List["ReportModel"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    jobs: Mapped[List["JobModel"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UploadModel(Base):
    __tablename__ = "uploads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    row_count: Mapped[Optional[int]] = mapped_column(Integer)
    column_count: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped[Optional["UserModel"]] = relationship(back_populates="uploads")
    jobs: Mapped[List["JobModel"]] = relationship(back_populates="upload", cascade="all, delete-orphan")
    reports: Mapped[List["ReportModel"]] = relationship(back_populates="upload", cascade="all, delete-orphan")


class JobModel(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    upload_id: Mapped[str] = mapped_column(ForeignKey("uploads.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=JobStatusEnum.PENDING.value, index=True, nullable=False)
    current_agent: Mapped[Optional[str]] = mapped_column(String(100))
    progress_pct: Mapped[float] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped[Optional["UserModel"]] = relationship(back_populates="jobs")
    upload: Mapped["UploadModel"] = relationship(back_populates="jobs")
    report: Mapped[Optional["ReportModel"]] = relationship(back_populates="job", uselist=False)


class ReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    upload_id: Mapped[str] = mapped_column(ForeignKey("uploads.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    cleaning_summary: Mapped[Optional[dict]] = mapped_column(JSONB if not _is_sqlite else Text, nullable=True)
    findings: Mapped[Optional[dict]] = mapped_column(JSONB if not _is_sqlite else Text, nullable=True)
    chart_paths: Mapped[Optional[dict]] = mapped_column(JSONB if not _is_sqlite else Text, nullable=True)
    report_markdown: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped[Optional["UserModel"]] = relationship(back_populates="reports")
    upload: Mapped["UploadModel"] = relationship(back_populates="reports")
    job: Mapped["JobModel"] = relationship(back_populates="report")
