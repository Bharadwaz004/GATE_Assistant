"""
Study plan API routes: generation, daily view, task updates, progress.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.schemas import (
    DailyPlanResponse,
    GeneratePlanRequest,
    ProgressMetrics,
    StreakResponse,
    UpdateTaskRequest,
    WeeklyPlanResponse,
)
from app.services.plan_service import get_study_plan_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/plan", tags=["Study Plan"])


@router.post("/generate", response_model=WeeklyPlanResponse)
async def generate_plan(
    request: GeneratePlanRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a weekly study plan using AI."""
    service = get_study_plan_service()
    return await service.generate_plan(db, user, request)


@router.get("/daily", response_model=DailyPlanResponse)
async def get_daily_plan(
    target_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the study plan for today or a specific date."""
    service = get_study_plan_service()
    parsed_date = date.fromisoformat(target_date) if target_date else None
    return await service.get_daily_plan(db, user, parsed_date)


@router.post("/task")
async def update_task(
    request: UpdateTaskRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a task as completed or skipped."""
    service = get_study_plan_service()
    return await service.update_task(db, user, request)


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    user: User = Depends(get_current_user),
):
    """Get current streak information."""
    service = get_study_plan_service()
    return await service.get_streak(str(user.id))


@router.get("/progress", response_model=ProgressMetrics)
async def get_progress(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive progress metrics."""
    service = get_study_plan_service()
    return await service.get_progress(db, user)
