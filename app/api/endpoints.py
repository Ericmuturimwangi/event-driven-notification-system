from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session 
from uuid import UUID
from app.core.dependencies import get_db
from app.schemas.event import EventCreateRequest, EventCreateResponse, EventResponse
from app.services.event_service import EventService
from app.workers.celery_app import celery_app
from app.workers.tasks import process_notification

router = APIRouter(
    prefix='/events',
    tags=["events"],
)

@router.post(
    "",
    response_model=EventCreateRequest,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a notification event",
    description="""
    Create a notification event and queue it for async processing.

    Returns 202 Accepted with event ID immediately.
    The actual notification processing happens asynchronously
    """,
)

async def create_event(
    request: EventCreateRequest,
    db: Session = Depends(get_db),
) -> EventCreateResponse:

    try:
        event = EventService.create_event(db, request)

        process_notification.delay(
            event_id=str(event.id), 
            event_type=event.event_type, 
            recipient = event.recipient, 
            payload = event.payload, 
        )

        return EventCreateResponse(
            id=event.id,
            status=event.status,
                    
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}",
        )

@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Retrieve event details",
    description="Get the current status and details of an event",
)

async def get_event(
    event_id: UUID,
    db: Session = Depends(get_db),
) -> EventResponse:

    event = EventService.get_event(db, event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found",
        )

    return EventResponse.from_orm(event)

    

