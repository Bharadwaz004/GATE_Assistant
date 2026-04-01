"""
Analytics service — tracks performance metrics, weak topic identification,
and improvement trends for dashboard visualization.
"""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import Integer, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import StudyTask, TaskStatusEnum, UserProfile

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Computes study analytics and identifies weak areas."""

    async def get_daily_study_hours(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get daily study hours for the last N days.
        Returns a list of {date, hours} for charting.
        """
        start = date.today() - timedelta(days=days)

        result = await db.execute(
            select(
                StudyTask.scheduled_date,
                func.sum(StudyTask.duration_minutes).label("total_minutes"),
            )
            .where(
                StudyTask.user_id == user_id,
                StudyTask.status == TaskStatusEnum.COMPLETED.value,
                StudyTask.scheduled_date >= start,
            )
            .group_by(StudyTask.scheduled_date)
            .order_by(StudyTask.scheduled_date)
        )

        return [
            {
                "date": row.scheduled_date.isoformat(),
                "hours": round(row.total_minutes / 60, 1),
            }
            for row in result.all()
        ]

    async def get_subject_breakdown(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get a breakdown of study time by subject.
        Returns sorted list for pie/bar chart visualization.
        """
        result = await db.execute(
            select(
                StudyTask.subject,
                func.count(StudyTask.id).label("total_tasks"),
                func.sum(
                    cast(
                        StudyTask.status == TaskStatusEnum.COMPLETED.value,
                        Integer,
                    )
                ).label("completed"),
                func.sum(StudyTask.duration_minutes).label("total_minutes"),
            )
            .where(StudyTask.user_id == user_id)
            .group_by(StudyTask.subject)
            .order_by(func.count(StudyTask.id).desc())
        )

        return [
            {
                "subject": row.subject,
                "total_tasks": row.total_tasks,
                "completed": row.completed or 0,
                "total_hours": round((row.total_minutes or 0) / 60, 1),
                "completion_rate": round(
                    (row.completed or 0) / max(row.total_tasks, 1) * 100, 1
                ),
            }
            for row in result.all()
        ]

    async def identify_weak_topics(
        self,
        db: AsyncSession,
        user_id: UUID,
        threshold: float = 50.0,
    ) -> List[Dict[str, Any]]:
        """
        Identify weak topics based on completion rate below threshold.
        Used for smart rescheduling and weak topic prioritization.
        """
        result = await db.execute(
            select(
                StudyTask.subject,
                StudyTask.topic,
                func.count(StudyTask.id).label("total"),
                func.sum(
                    cast(
                        StudyTask.status == TaskStatusEnum.COMPLETED.value,
                        Integer,
                    )
                ).label("completed"),
                func.sum(
                    cast(
                        StudyTask.status == TaskStatusEnum.SKIPPED.value,
                        Integer,
                    )
                ).label("skipped"),
            )
            .where(StudyTask.user_id == user_id)
            .group_by(StudyTask.subject, StudyTask.topic)
            .having(
                func.sum(
                    cast(
                        StudyTask.status == TaskStatusEnum.COMPLETED.value,
                        Integer,
                    )
                )
                / func.count(StudyTask.id)
                * 100
                < threshold
            )
            .order_by(
                (
                    func.sum(
                        cast(
                            StudyTask.status == TaskStatusEnum.COMPLETED.value,
                            Integer,
                        )
                    )
                    / func.count(StudyTask.id)
                ).asc()
            )
        )

        return [
            {
                "subject": row.subject,
                "topic": row.topic,
                "total_attempts": row.total,
                "completed": row.completed or 0,
                "skipped": row.skipped or 0,
                "completion_rate": round(
                    (row.completed or 0) / max(row.total, 1) * 100, 1
                ),
            }
            for row in result.all()
        ]

    async def get_improvement_trend(
        self,
        db: AsyncSession,
        user_id: UUID,
        weeks: int = 8,
    ) -> List[Dict[str, Any]]:
        """
        Compute weekly improvement trend.
        Shows completion rate, study hours, and consistency over time.
        """
        trends = []
        today = date.today()

        for i in range(weeks):
            week_end = today - timedelta(days=i * 7)
            week_start = week_end - timedelta(days=6)

            result = await db.execute(
                select(
                    func.count(StudyTask.id).label("total"),
                    func.sum(
                        cast(
                            StudyTask.status == TaskStatusEnum.COMPLETED.value,
                            Integer,
                        )
                    ).label("completed"),
                    func.sum(
                        func.case(
                            (
                                StudyTask.status == TaskStatusEnum.COMPLETED.value,
                                StudyTask.duration_minutes,
                            ),
                            else_=0,
                        )
                    ).label("study_minutes"),
                )
                .where(
                    StudyTask.user_id == user_id,
                    StudyTask.scheduled_date >= week_start,
                    StudyTask.scheduled_date <= week_end,
                )
            )

            row = result.one()
            total = row.total or 0
            completed = row.completed or 0
            study_minutes = row.study_minutes or 0

            # Count active study days
            days_result = await db.execute(
                select(func.count(func.distinct(StudyTask.scheduled_date)))
                .where(
                    StudyTask.user_id == user_id,
                    StudyTask.status == TaskStatusEnum.COMPLETED.value,
                    StudyTask.scheduled_date >= week_start,
                    StudyTask.scheduled_date <= week_end,
                )
            )
            active_days = days_result.scalar() or 0

            trends.append({
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "week_label": f"W{weeks - i}",
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": round(completed / max(total, 1) * 100, 1),
                "study_hours": round(study_minutes / 60, 1),
                "active_days": active_days,
                "consistency": round(active_days / 7 * 100, 1),
            })

        return list(reversed(trends))


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()
