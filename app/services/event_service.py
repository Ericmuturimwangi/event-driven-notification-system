from sqlalchemy.orm import Session
from uuid import UUID
from app.models.event import Event, EventStatus
from app.schemas.event import EventCreateRequest

class EventService:

    @staticmethod
    def create_event(
        db:Session,
        event_data: EventCreateRequest,
    ) -> Event:

        event = Event(
            event_type = event_data.event_type,
            recipient = event_data.recipient,
            payload=event_data.payload or {},
            status=EventStatus.PENDING,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return event

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
