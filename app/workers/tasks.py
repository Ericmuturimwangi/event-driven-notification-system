import logging
from uuid import UUID
from app.workers.celery_app import celery_app
from app.services.notification_service import NotificationService
from app.services.event_service import EventService
from app.models.event import EventStatus
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

@celery_app.task(
    name = "process_notification",
    max_retries=0,
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

    try:
        logger.info(f"[Task] Starting process_notification for event {event_id}")

        logger.info(f"[Task] Updating event {event_id} to PROCESSING")
        EventService.update_status(db, event_uuid, EventStatus.PROCESSING)

        logger.info(f"[Task] Sending {event_type} to {recipient}")
        success = NotificationService.send(
            event_type = event_type,
            recipient = recipient,
            payload=payload,
        )

        if not success:
            logger.error(f"[Task] Failed to send {event_type} to {recipient}")
            EventService.update_status(db, event_uuid, EventStatus.FAILED)
            return {
                "status": "failed",
                "event_id": event_id,
                "message": "Notification sending failed",
            }

        logger.info(f"[Task] Marking event {event_id} as COMPLETED")
        EventService.update_status(db, event_uuid, EventStatus.COMPLETED)

        logger.info(f"[Task] Successfully processed event {event_id}")

        return {
            "status": "success",
            "event_id": event_id,
            "message": f"Notification sent to {recipient}",
        }

    except Exception as e:
        logger.error(f"[Task] Error processing event {event_id}: {str(e)}")
        try:
            EventService.update_status(db, event_uuid, EventStatus.FAILED)
        except Exception as update_error:
            logger.error(f"[Task] Failed to update status: {str(update_error)}")

        return{
            "status": "failed",
            "event_id": event_id,
            "message": f"Task failed: {str(e)}",
        }

    finally:
        db.close()

        