
from src.core.celery_app import celery_app


@celery_app.task(name="src.tasks.test_tasks.add")
def add(x: int, y: int) -> int:
    return x + y
