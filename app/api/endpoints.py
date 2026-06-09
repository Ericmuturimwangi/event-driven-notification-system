from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session 
from uuid import UUID
from app.core.dependencies import get_db
from app.schemas.event import EventCreateRequest, EventCreateResponse, EventResponse, FailedEventResponse
from app.services.event_service import EventService
from app.workers.celery_app import celery_app
from app.workers.tasks import process_notification

router = APIRouter(
    prefix='/events',
    tags=["events"],
)

@router.post(
    "",
    response_model=EventCreateResponse,
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


@router.get(
    "/dlq/failed",
    response_model=list[FailedEventResponse],
    summary="View Dead Letter Queue",
    description = "Inspect failed events that exhausted retries. Use for operational debugging.",
)

async def get_dlq_events(
    event_type: str = Query(None, description="Filter by event type"),
    limit: int = Query(100, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
) -> list[FailedEventResponse]:


    failed_events = EventService.get_dlq_event(
        db,
        event_type=event_type,
        limit = limit,
        offset = offset,
    )

    return [FailedEventResponse.from_orm(fe) for fe in failed_events]



@router.get(
    "/dlq/failed/{failed_event_id}",
    response_model=FailedEventResponse,
    summary="Get specific DLQ event details",
)


async def get_dlq_event(
    failed_event_id : UUID,
    db: Session = Depends(get_db),
) -> FailedEventResponse:

    failed_event = EventService.get_dlq_event(db, failed_event_id)


    if not failed_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DLQ event {failed_event_id} not found",
        )

    return FailedEventResponse.from_orm(failed_event)



@router.post(
    "/dlq/replay/{failed_event_id}",
    response_model=EventCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Replay a failed event",
    description="Re-queue a failed event for processing. Use after fixing the underlying issue.",
)

async def replay_dlq_event(
    failed_event_id: UUID,
    db: Session = Depends(get_db),
) -> EventCreateResponse:

    try:
        failed_event = EventService.get_dlq_event(db, failed_event_id)
        if not failed_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"DLQ event {failed_event_id} not found",
            )

        replay_request = EventCreateRequest(
            event_type = failed_event.event_type,
            recipient = failed_event.recipient,
            payload= failed_event.payload,
        )

        new_event = EventService.create_event(db, replay_request)

        process_notification.delay(
            event_id =str(new_event.id),
            event_type=new_event.event_type,
            recipient=new_event.recipient,
            payload=new_event.payload,
        )

        return EventCreateResponse(
            id=new_event.id,
            status=new_event.status,
            message=f"Event replayed from DLQ {failed_event_id}",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to replay event: {str(e)}",
        )

        
