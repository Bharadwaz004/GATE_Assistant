"""
SQLAlchemy ORM models for the GATE Study Planner.

Tables:
  - users              : Authentication and profile data
  - user_profiles      : Onboarding details (branch, prep type, etc.)
  - study_plans        : Generated study plans
  - study_tasks        : Individual tasks within plans
  - user_embeddings    : Sentence-transformer embeddings for matching
  - matching_scores    : Precomputed similarity scores
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


# ── Enums ────────────────────────────────────────────────────
import enum


class BranchEnum(str, enum.Enum):
    CSE = "CSE"
    ECE = "ECE"
    EE = "EE"
    ME = "ME"
    CE = "CE"
    CH = "CH"
    IN = "IN"
    PI = "PI"
    BT = "BT"
    MN = "MN"
    DA = "DA"
    XE = "XE"
    XL = "XL"


class PrepTypeEnum(str, enum.Enum):
    COACHING = "coaching"
    SELF_STUDY = "self_study"


class TaskStatusEnum(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    RESCHEDULED = "rescheduled"


# ── User Model ───────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    study_plans: Mapped[List["StudyPlan"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    embedding: Mapped[Optional["UserEmbedding"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


# ── User Profile (Onboarding Data) ──────────────────────────
class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    branch: Mapped[str] = mapped_column(String(10), nullable=False)
    prep_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    subjects: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)

    # Coaching-specific fields
    coaching_start_time: Mapped[Optional[str]] = mapped_column(String(10))
    coaching_end_time: Mapped[Optional[str]] = mapped_column(String(10))
    available_study_slots: Mapped[Optional[dict]] = mapped_column(JSON)

    # Self-study-specific fields
    daily_available_hours: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="profile")


# ── Study Plan ───────────────────────────────────────────────
class StudyPlan(Base):
    __tablename__ = "study_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    plan_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="study_plans")
    tasks: Mapped[List["StudyTask"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


# ── Study Task ───────────────────────────────────────────────
class StudyTask(Base):
    __tablename__ = "study_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("study_plans.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    day_label: Mapped[str] = mapped_column(String(20), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    subtopic: Mapped[Optional[str]] = mapped_column(String(255))
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    timing: Mapped[Optional[str]] = mapped_column(String(50))
    task_type: Mapped[str] = mapped_column(
        String(20), default="study"
    )  # study, revision, mock_test, practice
    status: Mapped[str] = mapped_column(
        String(20), default=TaskStatusEnum.PENDING.value
    )
    rescheduled_to: Mapped[Optional[date]] = mapped_column(Date)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    plan: Mapped["StudyPlan"] = relationship(back_populates="tasks")


# ── User Embedding (for Matching) ────────────────────────────
class UserEmbedding(Base):
    __tablename__ = "user_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    embedding_vector: Mapped[list] = mapped_column(
        JSON, nullable=False
    )  # Stored as JSON array of floats
    profile_text: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="embedding")


# ── Matching Scores ──────────────────────────────────────────
class MatchingScore(Base):
    __tablename__ = "matching_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    matched_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
