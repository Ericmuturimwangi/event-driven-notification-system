import logging
import traceback
from uuid import UUID
from app.workers.celery_app import celery_app
from app.notification_service import NotificationService
from app.services.event_service import EventService
from app.models.event import EventStatus
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

@celery_app.task(
    name = "process_notification",
    max_retries=3,
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
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
    retry_count = self.request.retries

    try:
        logger.info(
            f"[Task] Processing event {event_id} (attempt {retry_count + 1}/4)"
        )

        event = EventService.get_event(db, event_uuid)
        if not event:
            logger.error(f"[Task] Event {event_id} not found in database")
            raise ValueError(f"Event {event_id} not found")

        logger.info(f"[Task] Updating event {event_id} to PROCESSING")
        EventService.update_status(db, event_uuid, EventStatus.PROCESSING)

        logger.info(f"[Task] Sending {event_type} to {recipient}")
        success = NotificationService.send(
            event_type=event_type,
            recipient=recipient,
            payload=payload,
            retry_count=retry_count,
        )

        if not success:
            logger.error(
                f"[Task] Failed to send {event_type} to {recipient}. Retrying..."
            )

            raise Exception(f"Notification service returned False for {event_type}")


        logger.info(f"[Task] Marking event {event_id} as COMPLETED")
        EventService.update_status(db, event_uuid, EventStatus.COMPLETED)

        logger.info(f"[Task] Successfully processed event {event_id}")

        return {

            "status": "success",
            "event_id": event_id,
            "message": f"Notification sent to {recipient}",
            "retry_count": retry_count,
        }



    except Exception as e:
        if retry_count < self.max_retries:
            logger.warning(
                f"[Task] Error processing event {event_id} (attempt {retry_count + 1}): {str(e)}"
            )
            raise self.retry(exc=e, countdown=2 ** (retry_count + 2))

        logger.error(
            f"[Task] Event {event_id} exhausted max retries ({self.max_retries}). Moving to DLQ."
        )

        try:
            error_tb = traceback.format_exc()
            failed_event = EventService.move_to_dlq(
                db,
                event_uuid,
                error_message=f"Task failed after {self.max_retries} retries.",
                error_traceback= error_tb,
                retry_count=retry_count,
                max_retries=self.max_retries,
            )

            logger.error(
                f"[Task] Event {event_id} moved to DLQ (record: {failed_event.id})"
            )
        except Exception as dlq_error:
            logger.error(f"[Task] Failed to move event to DLQ: {str(dlq_error)}")

        return {
            "status": "dlq",
            "event_id": event_id,
            "message": f"Task failed after {self.max_retries} retries. Moved to DLQ.",
        }

    finally:
        db.close()

        