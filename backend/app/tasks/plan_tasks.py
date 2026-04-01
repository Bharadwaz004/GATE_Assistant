"""
Background tasks for study plan generation and rescheduling.
Offloads heavy AI inference from the request/response cycle.
"""

import asyncio
import logging
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.db import async_session

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine in a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="app.tasks.plan_tasks.generate_plan_async",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def generate_plan_async(self, user_id: str, week_number: int):
    """
    Generate a weekly study plan in the background.
    Updates the database and Redis cache when complete.
    """
    logger.info(f"[Task] Generating plan for user={user_id}, week={week_number}")

    async def _generate():
        from app.ai.planner_service import get_planner_service
        from app.db.redis import get_redis_service
        from app.models import StudyPlan, StudyTask, TaskStatusEnum, UserProfile

        async with async_session() as db:
            # Fetch profile
            result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            if not profile:
                logger.error(f"No profile found for user {user_id}")
                return {"status": "error", "detail": "Profile not found"}

            planner = get_planner_service()
            redis = get_redis_service()

            today = date.today()
            start_date = today + timedelta(days=(week_number - 1) * 7)
            end_date = start_date + timedelta(days=6)

            daily_hours = profile.daily_available_hours or 6.0

            # Get context from previous tasks
            completed_result = await db.execute(
                select(StudyTask.topic).where(
                    StudyTask.user_id == user_id,
                    StudyTask.status == TaskStatusEnum.COMPLETED.value,
                ).distinct()
            )
            completed_topics = [r[0] for r in completed_result.all()]

            skipped_result = await db.execute(
                select(StudyTask.topic).where(
                    StudyTask.user_id == user_id,
                    StudyTask.status == TaskStatusEnum.SKIPPED.value,
                ).distinct()
            )
            skipped_topics = [r[0] for r in skipped_result.all()]

            # Generate plan
            plan_data = await planner.generate_weekly_plan(
                branch=profile.branch,
                subjects=profile.subjects or [],
                prep_type=profile.prep_type,
                daily_hours=daily_hours,
                week_number=week_number,
                start_date=start_date,
                coaching_start=profile.coaching_start_time,
                coaching_end=profile.coaching_end_time,
                completed_topics=completed_topics,
                skipped_topics=skipped_topics,
            )

            # Store plan
            study_plan = StudyPlan(
                user_id=user_id,
                plan_data=plan_data,
                week_number=week_number,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
            )
            db.add(study_plan)
            await db.flush()

            # Create task records
            import re
            for day_entry in plan_data:
                day_date_str = day_entry.get("date", start_date.isoformat())
                day_date = date.fromisoformat(day_date_str) if day_date_str else start_date

                for task in day_entry.get("tasks", []):
                    dur_str = str(task.get("duration", "1h")).strip().lower()
                    h = re.search(r"(\d+\.?\d*)\s*h", dur_str)
                    m = re.search(r"(\d+)\s*m", dur_str)
                    minutes = 0
                    if h:
                        minutes += int(float(h.group(1)) * 60)
                    if m:
                        minutes += int(m.group(1))
                    if minutes == 0:
                        minutes = 60

                    db.add(StudyTask(
                        plan_id=study_plan.id,
                        user_id=user_id,
                        day_label=day_entry["day"],
                        scheduled_date=day_date,
                        subject=task["subject"],
                        topic=task["topic"],
                        subtopic=task.get("subtopic"),
                        duration_minutes=minutes,
                        timing=task.get("timing"),
                        task_type=task.get("task_type", "study"),
                        status=TaskStatusEnum.PENDING.value,
                    ))

            await db.commit()

            # Cache daily plans
            for day_entry in plan_data:
                if day_entry.get("date"):
                    await redis.cache_daily_plan(user_id, day_entry["date"], day_entry)

            logger.info(f"[Task] Plan generated successfully for user={user_id}")
            return {"status": "success", "plan_id": str(study_plan.id)}

    try:
        return _run_async(_generate())
    except Exception as exc:
        logger.error(f"[Task] Plan generation failed: {exc}")
        self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.plan_tasks.reschedule_skipped_tasks",
    bind=True,
    max_retries=2,
)
def reschedule_skipped_tasks(self, user_id: str):
    """
    Find all skipped tasks and reschedule them using AI.
    """
    logger.info(f"[Task] Rescheduling skipped tasks for user={user_id}")

    async def _reschedule():
        from app.ai.planner_service import get_planner_service
        from app.models import StudyPlan, StudyTask, TaskStatusEnum, UserProfile

        async with async_session() as db:
            # Get skipped tasks
            result = await db.execute(
                select(StudyTask).where(
                    StudyTask.user_id == user_id,
                    StudyTask.status == TaskStatusEnum.SKIPPED.value,
                    StudyTask.rescheduled_to.is_(None),
                )
            )
            skipped = result.scalars().all()

            if not skipped:
                return {"status": "no_tasks", "detail": "No skipped tasks to reschedule"}

            # Get profile for daily hours
            profile_result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = profile_result.scalar_one_or_none()
            daily_hours = profile.daily_available_hours if profile else 6.0

            # Get existing upcoming tasks
            today = date.today()
            upcoming_result = await db.execute(
                select(StudyTask).where(
                    StudyTask.user_id == user_id,
                    StudyTask.scheduled_date > today,
                    StudyTask.status == TaskStatusEnum.PENDING.value,
                ).limit(20)
            )
            upcoming = upcoming_result.scalars().all()

            # Prepare data for AI
            skipped_data = [
                {"subject": t.subject, "topic": t.topic, "duration": f"{t.duration_minutes}m"}
                for t in skipped
            ]
            existing_data = [
                {
                    "day": t.day_label, "subject": t.subject,
                    "topic": t.topic, "duration": f"{t.duration_minutes}m",
                }
                for t in upcoming
            ]

            planner = get_planner_service()

            # Calculate remaining days until exam (cap at 14)
            if profile and profile.target_exam_date:
                remaining = min(14, (profile.target_exam_date - today).days)
            else:
                remaining = 7

            rescheduled = await planner.reschedule_tasks(
                skipped_tasks=skipped_data,
                remaining_days=remaining,
                daily_hours=daily_hours,
                existing_tasks=existing_data,
            )

            # Get active plan
            plan_result = await db.execute(
                select(StudyPlan).where(
                    StudyPlan.user_id == user_id,
                    StudyPlan.is_active == True,
                ).order_by(StudyPlan.created_at.desc()).limit(1)
            )
            active_plan = plan_result.scalar_one_or_none()

            # Create new task records
            created = 0
            for task_data in rescheduled:
                sched_date_str = task_data.get("scheduled_date")
                if not sched_date_str:
                    continue

                import re
                dur_str = str(task_data.get("duration", "1h")).strip().lower()
                h = re.search(r"(\d+\.?\d*)\s*h", dur_str)
                m = re.search(r"(\d+)\s*m", dur_str)
                minutes = 0
                if h:
                    minutes += int(float(h.group(1)) * 60)
                if m:
                    minutes += int(m.group(1))
                if minutes == 0:
                    minutes = 60

                db.add(StudyTask(
                    plan_id=active_plan.id if active_plan else skipped[0].plan_id,
                    user_id=user_id,
                    day_label="Rescheduled",
                    scheduled_date=date.fromisoformat(sched_date_str),
                    subject=task_data["subject"],
                    topic=task_data["topic"],
                    subtopic=task_data.get("subtopic"),
                    duration_minutes=minutes,
                    timing=task_data.get("timing"),
                    task_type=task_data.get("task_type", "study"),
                    status=TaskStatusEnum.PENDING.value,
                ))
                created += 1

            # Mark originals as rescheduled
            for task in skipped:
                task.status = TaskStatusEnum.RESCHEDULED.value

            await db.commit()
            logger.info(f"[Task] Rescheduled {created} tasks for user={user_id}")
            return {"status": "success", "rescheduled_count": created}

    try:
        return _run_async(_reschedule())
    except Exception as exc:
        logger.error(f"[Task] Rescheduling failed: {exc}")
        self.retry(exc=exc)
