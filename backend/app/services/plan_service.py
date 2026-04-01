"""
Study plan service: orchestrates AI plan generation, task CRUD, and analytics.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.planner_service import get_planner_service
from app.db.redis import get_redis_service
from app.models import StudyPlan, StudyTask, TaskStatusEnum, User, UserProfile
from app.schemas import (
    DailyPlan,
    DailyPlanResponse,
    GeneratePlanRequest,
    ProgressMetrics,
    StreakResponse,
    TaskItem,
    UpdateTaskRequest,
    WeeklyPlanResponse,
)

logger = logging.getLogger(__name__)


class StudyPlanService:
    """Manages study plan generation, task updates, and progress tracking."""

    def __init__(self):
        self.planner = get_planner_service()
        self.redis = get_redis_service()

    # ── Plan Generation ──────────────────────────────────────
    async def generate_plan(
        self,
        db: AsyncSession,
        user: User,
        request: GeneratePlanRequest,
    ) -> WeeklyPlanResponse:
        """
        Generate a weekly study plan using AI.
        Stores the plan and individual tasks in the database.
        """
        # Get user profile
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Complete onboarding first",
            )

        # Calculate week start date
        today = date.today()
        week_offset = (request.week_number - 1) * 7
        start_date = today + timedelta(days=week_offset)
        end_date = start_date + timedelta(days=6)

        # Check for existing active plan (unless force regenerate)
        if not request.force_regenerate:
            existing = await db.execute(
                select(StudyPlan).where(
                    StudyPlan.user_id == user.id,
                    StudyPlan.week_number == request.week_number,
                    StudyPlan.is_active == True,
                )
            )
            existing_plan = existing.scalar_one_or_none()
            if existing_plan:
                return await self._format_plan_response(db, existing_plan)

        # Get completed and skipped topics for context
        completed_topics = await self._get_completed_topics(db, user.id)
        skipped_topics = await self._get_skipped_topics(db, user.id)

        # Determine daily hours outside coaching
        if profile.prep_type == "coaching" and profile.coaching_start_time and profile.coaching_end_time:
            daily_hours = self._calc_free_hours(
                profile.coaching_start_time, profile.coaching_end_time
            )
        else:
            daily_hours = profile.daily_available_hours or 6.0

        # Parse study slots
        study_slots = None
        if profile.available_study_slots:
            study_slots = profile.available_study_slots

        # Generate plan via AI
        plan_data = await self.planner.generate_weekly_plan(
            branch=profile.branch,
            subjects=profile.subjects or [],
            prep_type=profile.prep_type,
            daily_hours=daily_hours,
            week_number=request.week_number,
            start_date=start_date,
            coaching_start=profile.coaching_start_time,
            coaching_end=profile.coaching_end_time,
            study_slots=study_slots,
            completed_topics=completed_topics,
            skipped_topics=skipped_topics,
        )

        # Delete tasks and deactivate old plans for this week
        old_plans = await db.execute(
            select(StudyPlan).where(
                StudyPlan.user_id == user.id,
                StudyPlan.week_number == request.week_number,
            )
        )
        for old_plan in old_plans.scalars().all():
            await db.execute(
                delete(StudyTask).where(StudyTask.plan_id == old_plan.id)
            )
            old_plan.is_active = False

        # Store new plan
        study_plan = StudyPlan(
            user_id=user.id,
            plan_data=plan_data,
            week_number=request.week_number,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
        )
        db.add(study_plan)
        await db.flush()

        # Create individual task records
        for day_entry in plan_data:
            day_date = date.fromisoformat(day_entry["date"]) if day_entry.get("date") else start_date
            for task in day_entry.get("tasks", []):
                duration_str = task.get("duration", "1h")
                minutes = self._parse_duration_minutes(duration_str)

                study_task = StudyTask(
                    plan_id=study_plan.id,
                    user_id=user.id,
                    day_label=day_entry["day"],
                    scheduled_date=day_date,
                    subject=task["subject"],
                    topic=task["topic"],
                    subtopic=task.get("subtopic"),
                    duration_minutes=minutes,
                    timing=task.get("timing"),
                    task_type=task.get("task_type", "study"),
                    status=TaskStatusEnum.PENDING.value,
                )
                db.add(study_task)

        await db.flush()

        # Cache daily plan
        for day_entry in plan_data:
            if day_entry.get("date"):
                await self.redis.cache_daily_plan(
                    str(user.id), day_entry["date"], day_entry
                )

        return await self._format_plan_response(db, study_plan)

    # ── Daily Plan ───────────────────────────────────────────
    async def get_daily_plan(
        self,
        db: AsyncSession,
        user: User,
        target_date: Optional[date] = None,
    ) -> DailyPlanResponse:
        """Get the study plan for a specific day."""
        target = target_date or date.today()
        date_str = target.isoformat()

        # Check Redis cache first
        cached = await self.redis.get_cached_daily_plan(str(user.id), date_str)
        if cached and not target_date:
            tasks = []
            for t in cached.get("tasks", []):
                tasks.append(TaskItem(
                    subject=t["subject"],
                    topic=t["topic"],
                    subtopic=t.get("subtopic"),
                    duration=t.get("duration", "1h"),
                    timing=t.get("timing"),
                    task_type=t.get("task_type", "study"),
                    status=t.get("status", "pending"),
                ))

        # Fetch from database (only tasks belonging to an active plan)
        result = await db.execute(
            select(StudyTask)
            .join(StudyPlan, StudyTask.plan_id == StudyPlan.id)
            .where(
                StudyTask.user_id == user.id,
                StudyTask.scheduled_date == target,
                StudyPlan.is_active == True,
            )
            .order_by(StudyTask.timing)
        )
        db_tasks = result.scalars().all()

        tasks = []
        completed = 0
        total_minutes = 0

        for t in db_tasks:
            tasks.append(TaskItem(
                id=str(t.id),
                subject=t.subject,
                topic=t.topic,
                subtopic=t.subtopic,
                duration=f"{t.duration_minutes}m",
                timing=t.timing,
                task_type=t.task_type,
                status=t.status,
            ))
            total_minutes += t.duration_minutes
            if t.status == TaskStatusEnum.COMPLETED.value:
                completed += 1

        total = len(tasks)
        completion_rate = (completed / total * 100) if total > 0 else 0

        # Determine day label
        day_label = db_tasks[0].day_label if db_tasks else f"{target.strftime('%A')}"

        return DailyPlanResponse(
            date=date_str,
            day_label=day_label,
            tasks=tasks,
            completion_rate=round(completion_rate, 1),
            total_hours=round(total_minutes / 60, 1),
        )

    # ── Task Update ──────────────────────────────────────────
    async def update_task(
        self,
        db: AsyncSession,
        user: User,
        request: UpdateTaskRequest,
    ) -> dict:
        """
        Mark a task as completed or skipped.
        Handles streak updates and rescheduling.
        """
        result = await db.execute(
            select(StudyTask).where(
                StudyTask.id == request.task_id,
                StudyTask.user_id == user.id,
            )
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        task.status = request.status
        task.notes = request.notes

        if request.status == TaskStatusEnum.COMPLETED.value:
            task.completed_at = datetime.now(timezone.utc)

            # Check if all tasks for today are completed → update streak
            today_str = date.today().isoformat()
            today_tasks = await db.execute(
                select(StudyTask).where(
                    StudyTask.user_id == user.id,
                    StudyTask.scheduled_date == date.today(),
                )
            )
            all_today = today_tasks.scalars().all()

            completed_count = sum(
                1 for t in all_today if t.status == TaskStatusEnum.COMPLETED.value
            )
            total_count = len(all_today)

            # Update streak if >80% tasks completed
            if total_count > 0 and (completed_count / total_count) >= 0.8:
                await self.redis.update_streak(str(user.id), today_str)

        elif request.status == TaskStatusEnum.SKIPPED.value:
            # Mark for rescheduling
            task.status = TaskStatusEnum.SKIPPED.value

        await db.flush()

        # Invalidate daily plan cache
        await self.redis.delete_cache(
            f"daily_plan:{user.id}:{task.scheduled_date.isoformat()}"
        )

        return {
            "task_id": str(task.id),
            "status": task.status,
            "message": f"Task marked as {request.status}",
        }

    # ── Streak ───────────────────────────────────────────────
    async def get_streak(self, user_id: str) -> StreakResponse:
        """Get current streak information from Redis."""
        streak_data = await self.redis.get_streak(user_id)
        return StreakResponse(
            current_streak=streak_data["current"],
            longest_streak=streak_data["longest"],
            last_active_date=streak_data["last_date"],
        )

    # ── Progress Metrics ─────────────────────────────────────
    async def get_progress(
        self,
        db: AsyncSession,
        user: User,
    ) -> ProgressMetrics:
        """Calculate comprehensive progress metrics."""
        # Total tasks
        result = await db.execute(
            select(func.count(StudyTask.id)).where(StudyTask.user_id == user.id)
        )
        total_tasks = result.scalar() or 0

        # Completed tasks
        result = await db.execute(
            select(func.count(StudyTask.id)).where(
                StudyTask.user_id == user.id,
                StudyTask.status == TaskStatusEnum.COMPLETED.value,
            )
        )
        completed_tasks = result.scalar() or 0

        # Skipped tasks
        result = await db.execute(
            select(func.count(StudyTask.id)).where(
                StudyTask.user_id == user.id,
                StudyTask.status == TaskStatusEnum.SKIPPED.value,
            )
        )
        skipped_tasks = result.scalar() or 0

        # Total study hours (completed tasks only)
        result = await db.execute(
            select(func.sum(StudyTask.duration_minutes)).where(
                StudyTask.user_id == user.id,
                StudyTask.status == TaskStatusEnum.COMPLETED.value,
            )
        )
        total_minutes = result.scalar() or 0

        # Subject-wise progress
        subject_progress = await self._get_subject_progress(db, user.id)

        # Weekly trend (last 4 weeks)
        weekly_trend = await self._get_weekly_trend(db, user.id)

        # Streak
        streak = await self.get_streak(str(user.id))

        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return ProgressMetrics(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            skipped_tasks=skipped_tasks,
            completion_rate=round(completion_rate, 1),
            total_study_hours=round(total_minutes / 60, 1),
            streak=streak,
            subject_progress=subject_progress,
            weekly_trend=weekly_trend,
        )

    # ── Private Helpers ──────────────────────────────────────
    async def _format_plan_response(
        self, db: AsyncSession, plan: StudyPlan
    ) -> WeeklyPlanResponse:
        """Format a StudyPlan model into the API response schema."""
        days = []
        for day_data in plan.plan_data:
            tasks = [
                TaskItem(
                    subject=t["subject"],
                    topic=t["topic"],
                    subtopic=t.get("subtopic"),
                    duration=t.get("duration", "1h"),
                    timing=t.get("timing"),
                    task_type=t.get("task_type", "study"),
                    status=t.get("status", "pending"),
                )
                for t in day_data.get("tasks", [])
            ]
            days.append(DailyPlan(
                day=day_data["day"],
                date=day_data.get("date"),
                tasks=tasks,
                total_hours=day_data.get("total_hours"),
            ))

        return WeeklyPlanResponse(
            plan_id=str(plan.id),
            week_number=plan.week_number,
            start_date=plan.start_date.isoformat(),
            end_date=plan.end_date.isoformat(),
            days=days,
        )

    def _calc_free_hours(self, coaching_start: str, coaching_end: str) -> float:
        """Return study hours available outside coaching (before + after)."""
        from datetime import datetime as dt
        fmt_candidates = ["%I:%M %p", "%H:%M", "%I %p"]
        def parse(t):
            for fmt in fmt_candidates:
                try:
                    return dt.strptime(t.strip(), fmt)
                except ValueError:
                    continue
            return None

        start = parse(coaching_start)
        end = parse(coaching_end)
        if not start or not end:
            return 4.0  # safe default

        day_start = dt.strptime("5:30 AM", "%I:%M %p")
        day_end = dt.strptime("10:00 PM", "%I:%M %p")

        before = max(0, (start - day_start).seconds / 3600)
        after = max(0, (day_end - end).seconds / 3600)
        return round(before + after, 1)

    async def _get_completed_topics(
        self, db: AsyncSession, user_id: UUID
    ) -> List[str]:
        result = await db.execute(
            select(StudyTask.topic).where(
                StudyTask.user_id == user_id,
                StudyTask.status == TaskStatusEnum.COMPLETED.value,
            ).distinct()
        )
        return [row[0] for row in result.all()]

    async def _get_skipped_topics(
        self, db: AsyncSession, user_id: UUID
    ) -> List[str]:
        result = await db.execute(
            select(StudyTask.topic).where(
                StudyTask.user_id == user_id,
                StudyTask.status == TaskStatusEnum.SKIPPED.value,
            ).distinct()
        )
        return [row[0] for row in result.all()]

    async def _get_subject_progress(
        self, db: AsyncSession, user_id: UUID
    ) -> Dict:
        """Calculate per-subject completion rates."""
        from sqlalchemy import Integer

        result = await db.execute(
            select(
                StudyTask.subject,
                func.count(StudyTask.id).label("total"),
                func.sum(
                    func.cast(
                        StudyTask.status == TaskStatusEnum.COMPLETED.value, Integer
                    )
                ).label("completed"),
            )
            .where(StudyTask.user_id == user_id)
            .group_by(StudyTask.subject)
        )

        progress = {}
        for row in result.all():
            total = row.total or 0
            completed = row.completed or 0
            progress[row.subject] = {
                "total": total,
                "completed": completed,
                "rate": round(completed / total * 100, 1) if total > 0 else 0,
            }
        return progress

    async def _get_weekly_trend(
        self, db: AsyncSession, user_id: UUID
    ) -> List[Dict]:
        """Get completion trend for the last 4 weeks."""
        trends = []
        today = date.today()

        from sqlalchemy import Integer

        for week_offset in range(4):
            week_start = today - timedelta(days=today.weekday() + 7 * week_offset)
            week_end = week_start + timedelta(days=6)

            result = await db.execute(
                select(
                    func.count(StudyTask.id).label("total"),
                    func.sum(
                        func.cast(
                            StudyTask.status == TaskStatusEnum.COMPLETED.value,
                            Integer,
                        )
                    ).label("completed"),
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

            trends.append({
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "total": total,
                "completed": completed,
                "rate": round(completed / total * 100, 1) if total > 0 else 0,
            })

        return list(reversed(trends))

    @staticmethod
    def _parse_duration_minutes(duration_str: str) -> int:
        """Parse '2h', '90m', '1.5h' to minutes."""
        import re
        duration_str = str(duration_str).strip().lower()
        h_match = re.search(r"(\d+\.?\d*)\s*h", duration_str)
        m_match = re.search(r"(\d+)\s*m", duration_str)
        minutes = 0
        if h_match:
            minutes += int(float(h_match.group(1)) * 60)
        if m_match:
            minutes += int(m_match.group(1))
        return minutes if minutes > 0 else 60


def get_study_plan_service() -> StudyPlanService:
    return StudyPlanService()
