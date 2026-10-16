
from celery import Celery

from src.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "rag_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Cairo",
    enable_utc=True,
    task_track_started=True,
)
celery_app.conf.imports = (
    "src.tasks.test_tasks",
    "src.tasks.document_tasks",
)