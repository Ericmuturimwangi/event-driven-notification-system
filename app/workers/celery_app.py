from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "event_notification",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],  # ensures process_notification is registered
)

celery_app.conf.update(

    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    timezone="UTC",
    enable_utc= True,

    task_track_started = True,
    task_time_limit=30 * 60,
    task_soft_time_limit = 25 *60,

    worker_prefetch_multiplier =4,
    worker_max_tasks_per_child = 1000,

)

@celery_app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")

    