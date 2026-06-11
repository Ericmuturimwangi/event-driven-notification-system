import logging
import random
from celery import Task
from celery.exceptions import MaxRetriesExceededError

import traceback
from uuid import UUID

from app.workers.celery_app import celery_app
from app.notification_service import NotificationService
from app.services.event_service import EventService
from app.models.event import EventStatus
from app.db.session import SessionLocal
from app.core.config import settings
from app.core.exceptions import PermanentNotificationError

logger = logging.getLogger(__name__)

def _backoff_with_jitter(retry_number: int) -> float:

    delay = settings.task_retry_base_delay + (2 ** retry_number)
    delay = min(delay, settings.task_retry_max_delay)
    return delay * random.uniform(0.8, 1.2)

class NotificationTask(Task):

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        event_id = kwargs.get("event_id") or (args[0] if args else None)
        if not event_id:
            logger.critical(
                f"[DLQ] Task {task_id} failed with no event_id in args/kwargs."
                f"Cannot reoute to DLQ. Error: {exc}"
            )

            return
        db = SessionLocal()

        try:
            failed_event = EventService.move_to_dlq(
                db,
                UUID(event_id),
                error_message=str(exc),
                error_traceback=str(einfo),
                retry_count=self.request.retries,
                max_retries=self.max_retries,
            )
            logger.error(
                f"[DLQ] Event {event_id} moved to DLQ"
                f"(record {failed_event.id}) after "
                f"{self.request.retries} retries: {exc}"
            )

        except Exception as dlq_error:

            logger.critical(
                f"[DLQ] FILED to move event {event_id} to DLQ: {dlq_error}. "
                F"Original error: {exc}"
            )
        finally:
            db.close()


@celery_app.task(
    name = "process_notification",
    max_retries=settings.task_max_retries,
    acks_late=True,
    base=NotificationTask,
    bind=True,

)

def process_notification(
    self, 
    event_id: str, 
    event_type: str, 
    recipient: str, 
    payload: dict, 
) -> dict: 

    db = SessionLocal()
    event_uuid = UUID(event_id)
    attempt = self.request.retries + 1
    total_attempts = self.max_retries + 1

    try:
        logger.info(
            f"[Task] Event {event_id} attempt {attempt}/{total_attempts}"
        )

        event = EventService.get_event(db, event_uuid)

        if not event:
            raise PermanentNotificationError(
                f"Event {event_id} not found in database"
            )

        if event.status == EventStatus.COMPLETED:
            logger.info(
                f"[Task] Event {event_id} already COMPLETED - "
                f"skipping redelivered task (idempotent consumer)"
            )

            return {
                "status": "skipped",
                "event_id": event_id,
                "reason": "already_completed",
            }

        EventService.update_status(db, event_uuid, EventStatus.PROCESSING)

        NotificationService.send(
            event_type=event_type,
            recipient=recipient,
            payload=payload,
        )

        EventService.update_status(db, event_uuid, EventStatus.COMPLETED)

        logger.info(
            f"[Task] Event {event_id} COMPLETED on attempt {attempt}"
        )

        return {
            "status": "success",
            "event_id": event_id,
            "attempt": attempt,
        }


    except PermanentNotificationError as exc:

        logger.error(
            f"[Task] Event {event_id}: PERMANENT failure, skipping retries: {exc}"
        )
        raise

    except Exception as exc:

        countdown = _backoff_with_jitter(self.request.retries)
        logger.warning(
            f"[Task] Event {event_id}: attempt {attempt}/{total_attempts} "
            f"failed ({exc}). Retrying in {countdown:.0f}s"
        )

        try:

            raise self.retry(exc=exc, countdown=countdown)

        except MaxRetriesExceededError:
            logger.error(
                f"[Task] Event {event_id}: retries exhausted "
                f"({self.max_retries}). Routing to DLQ"
            )

            raise exc
    finally:
        db.close()
