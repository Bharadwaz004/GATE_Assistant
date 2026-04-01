"""
Analytics API routes — performance tracking and trend data.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.services.analytics_service import get_analytics_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/daily-hours")
async def get_daily_hours(
    days: int = Query(default=30, ge=7, le=90),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily study hours for charting."""
    service = get_analytics_service()
    data = await service.get_daily_study_hours(db, user.id, days)
    return {"data": data, "period_days": days}


@router.get("/subject-breakdown")
async def get_subject_breakdown(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get study time breakdown by subject."""
    service = get_analytics_service()
    data = await service.get_subject_breakdown(db, user.id)
    return {"subjects": data}


@router.get("/weak-topics")
async def get_weak_topics(
    threshold: float = Query(default=50.0, ge=0, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Identify weak topics below a completion threshold."""
    service = get_analytics_service()
    topics = await service.identify_weak_topics(db, user.id, threshold)
    return {"weak_topics": topics, "threshold": threshold}


@router.get("/improvement-trend")
async def get_improvement_trend(
    weeks: int = Query(default=8, ge=4, le=16),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get weekly improvement trend data."""
    service = get_analytics_service()
    trend = await service.get_improvement_trend(db, user.id, weeks)
    return {"trend": trend, "period_weeks": weeks}
