"""
Pydantic v2 schemas for request validation and response serialization.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ═══════════════════════════════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════════════════════════════

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    is_onboarded: bool


# ═══════════════════════════════════════════════════════════════
# USER / PROFILE SCHEMAS
# ═══════════════════════════════════════════════════════════════

class StudySlot(BaseModel):
    start_time: str = Field(description="e.g., '14:00'")
    end_time: str = Field(description="e.g., '16:00'")
    label: Optional[str] = None


class OnboardingRequest(BaseModel):
    branch: str = Field(description="GATE branch code: CSE, ECE, DA, etc.")
    prep_type: str = Field(description="'coaching' or 'self_study'")
    target_exam_date: date
    subjects: List[str] = Field(min_length=1, description="Subjects to prepare")

    # Coaching-specific
    coaching_start_time: Optional[str] = None
    coaching_end_time: Optional[str] = None
    available_study_slots: Optional[List[StudySlot]] = None

    # Self-study-specific
    daily_available_hours: Optional[float] = None

    @field_validator("prep_type")
    @classmethod
    def validate_prep_type(cls, v: str) -> str:
        if v not in ("coaching", "self_study"):
            raise ValueError("prep_type must be 'coaching' or 'self_study'")
        return v

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v: str) -> str:
        valid = {"CSE", "ECE", "EE", "ME", "CE", "CH", "IN", "PI", "BT", "MN", "DA", "XE", "XL"}
        if v.upper() not in valid:
            raise ValueError(f"branch must be one of: {', '.join(sorted(valid))}")
        return v.upper()


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_onboarded: bool
    branch: Optional[str] = None
    prep_type: Optional[str] = None
    target_exam_date: Optional[date] = None
    subjects: Optional[List[str]] = None
    daily_available_hours: Optional[float] = None
    coaching_start_time: Optional[str] = None
    coaching_end_time: Optional[str] = None
    streak: Optional[Dict[str, Any]] = None


# ═══════════════════════════════════════════════════════════════
# STUDY PLAN SCHEMAS
# ═══════════════════════════════════════════════════════════════

class GeneratePlanRequest(BaseModel):
    week_number: int = Field(ge=1, description="Which week to generate")
    force_regenerate: bool = False


class TaskItem(BaseModel):
    id: Optional[str] = None
    subject: str
    topic: str
    subtopic: Optional[str] = None
    duration: str = Field(description="e.g., '2h' or '90m'")
    timing: Optional[str] = None
    task_type: str = "study"
    status: str = "pending"


class DailyPlan(BaseModel):
    day: str
    date: Optional[str] = None
    tasks: List[TaskItem]
    total_hours: Optional[float] = None


class WeeklyPlanResponse(BaseModel):
    plan_id: str
    week_number: int
    start_date: str
    end_date: str
    days: List[DailyPlan]
    summary: Optional[Dict[str, Any]] = None


class DailyPlanResponse(BaseModel):
    date: str
    day_label: str
    tasks: List[TaskItem]
    completion_rate: float
    total_hours: float


class UpdateTaskRequest(BaseModel):
    task_id: str
    status: str = Field(description="'completed' or 'skipped'")
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("completed", "skipped"):
            raise ValueError("status must be 'completed' or 'skipped'")
        return v


# ═══════════════════════════════════════════════════════════════
# STREAK SCHEMAS
# ═══════════════════════════════════════════════════════════════

class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    last_active_date: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# MATCHING SCHEMAS
# ═══════════════════════════════════════════════════════════════

class MatchedUser(BaseModel):
    user_id: str
    full_name: str
    branch: str
    prep_type: str
    subjects: List[str]
    similarity_score: float
    common_subjects: List[str]


class MatchingResponse(BaseModel):
    matches: List[MatchedUser]
    total_found: int


# ═══════════════════════════════════════════════════════════════
# ANALYTICS SCHEMAS
# ═══════════════════════════════════════════════════════════════

class ProgressMetrics(BaseModel):
    total_tasks: int
    completed_tasks: int
    skipped_tasks: int
    completion_rate: float
    total_study_hours: float
    streak: StreakResponse
    subject_progress: Dict[str, Dict[str, Any]]
    weekly_trend: List[Dict[str, Any]]
