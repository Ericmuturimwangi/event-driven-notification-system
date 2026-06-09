from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from app.models.event import Event, FailedEvent, EventStatus
from app.schemas.event import EventCreateRequest

class EventService:

    @staticmethod
    def create_event(
        db:Session,
        event_data: EventCreateRequest,
    ) -> Event:


        if event_data.idempotency_key:
            existing_event = db.query(Event).filter(
                Event.idempotency_key == event_data.idempotency_key
            ).first()

            if existing_event:

                return existing_event

        event = Event(
            event_type = event_data.event_type,
            recipient = event_data.recipient,
            payload=event_data.payload or {},
            status=EventStatus.PENDING,
            idempotency_key=event_data.idempotency_key,
        )

        try:

            db.add(event)
            db.commit()
            db.refresh(event)

            return event
        except IntegrityError as e:

            db.rollback()

            if event_data.idempotency_key:
                existing_event = db.query(Event).filter(
                    Event.idempotency_key == event_data.idempotency_key
                ).first()
                if existing_event:
                    return existing_event

    @staticmethod
    def update_status(
        db:Session,
        event_id: UUID,
        new_status: EventStatus,
    ) -> Event:

        event =db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ValueError(f"Event {event_id} not found")

        event.status = new_status
        db.commit()
        db.refresh(event)

        return event

    
    @staticmethod
    def get_event(db: Session, event_id: UUID) -> Event:

        return db.query(Event).filter(Event.id == event_id).first()


    @staticmethod
    def move_to_dlq(
        db: Session,
        event_id: UUID,
        error_message: str,
        error_traceback: str = None,
        retry_count: int = 0,
        max_retries: int = 3,
    ) -> FailedEvent:

        event = EventService.get_event(db, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        failed_event = FailedEvent(
            event_id=event_id,
            event_type=event.event_type,
            recipient = event.recipient,
            payload = event.payload,
            error_message = error_message,
            error_traceback = error_traceback,
            retry_count = retry_count,
            max_retries = max_retries,
        )

        db.add(failed_event)

        event.status = EventStatus.FAILED

        db.commit()
        db.refresh(failed_event)

        return failed_event


    @staticmethod

    def get_dlq_events(
        db:Session,
        event_type: str = None,
        limit: int = 100,
        offset: int =0,
    ) -> list[FailedEvent]:

        query = db.query(FailedEvent)

        if event_type:
            query = query.filter(FailedEvent.event_type == event_type)

        return query.order_by(FailedEvent.created_at.desc()).limit(limit).offset(offset).all()

    
    @staticmethod

    def get_dlq_event(db: Session, failed_event_id: UUID) -> FailedEvent:

        return db.query(FailedEvent).filter(FailedEvent.id == failed_event_id).first()
        
         
