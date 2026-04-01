"""
Celery application for background task processing.
Handles plan generation, embedding updates, and similarity recomputation.
"""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "gate_planner",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 min hard limit
    task_soft_time_limit=240,  # 4 min soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_routes={
        "app.tasks.plan_tasks.*": {"queue": "plan_generation"},
        "app.tasks.embedding_tasks.*": {"queue": "embeddings"},
        "app.tasks.matching_tasks.*": {"queue": "matching"},
    },
    task_default_queue="default",
)

celery_app.autodiscover_tasks(["app.tasks"])
