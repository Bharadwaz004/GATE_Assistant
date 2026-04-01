"""
Background tasks for embedding generation and matching score recomputation.
Runs after onboarding or profile updates.
"""

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.db import async_session

logger = logging.getLogger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="app.tasks.embedding_tasks.update_user_embedding",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def update_user_embedding(self, user_id: str):
    """
    Generate or update the sentence-transformer embedding for a user.
    Called after onboarding or profile update.
    """
    logger.info(f"[Task] Updating embedding for user={user_id}")

    async def _update():
        from app.models import UserProfile
        from app.services.matching_service import get_matching_service

        async with async_session() as db:
            result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()

            if not profile:
                logger.warning(f"No profile for user {user_id}")
                return {"status": "error", "detail": "Profile not found"}

            matching = get_matching_service()
            await matching.update_user_embedding(db, UUID(user_id), profile)
            await db.commit()

            logger.info(f"[Task] Embedding updated for user={user_id}")
            return {"status": "success"}

    try:
        return _run_async(_update())
    except Exception as exc:
        logger.error(f"[Task] Embedding update failed: {exc}")
        self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.embedding_tasks.recompute_all_matches",
    bind=True,
    max_retries=1,
)
def recompute_all_matches(self):
    """
    Recompute matching scores for all users.
    Scheduled to run periodically (e.g., every 6 hours).
    """
    logger.info("[Task] Recomputing all matching scores")

    async def _recompute():
        from app.models import User, UserEmbedding
        from app.services.matching_service import get_matching_service

        async with async_session() as db:
            # Get all users with embeddings
            result = await db.execute(
                select(UserEmbedding.user_id)
            )
            user_ids = [str(row[0]) for row in result.all()]

            matching = get_matching_service()
            updated_count = 0

            for uid in user_ids:
                try:
                    await matching.find_matches(db, UUID(uid), top_n=20)
                    updated_count += 1
                except Exception as e:
                    logger.warning(f"Failed to compute matches for {uid}: {e}")

            await db.commit()
            logger.info(f"[Task] Recomputed matches for {updated_count} users")
            return {"status": "success", "users_processed": updated_count}

    try:
        return _run_async(_recompute())
    except Exception as exc:
        logger.error(f"[Task] Match recomputation failed: {exc}")
        self.retry(exc=exc)


# ── Periodic Tasks Schedule ──────────────────────────────────
celery_app.conf.beat_schedule = {
    "recompute-matches-every-6h": {
        "task": "app.tasks.embedding_tasks.recompute_all_matches",
        "schedule": 6 * 60 * 60,  # Every 6 hours
    },
}
