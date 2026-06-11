from pydantic import BaseModel, Field, EmailStr
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from app.models.event import EventStatus

class EventCreateRequest(BaseModel):

    event_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Type of event (eg., 'email', 'sms')",
    )

    recipient: str = Field(
        ...,
        min_length=1, 
        max_length=255,
        description="Recipient identifier (email, phone, user ID, etc.)",
    )

    payload: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Event-specific data (JSON object)",
    )

    idempotency_key: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Idempotency key for request deduplication. UUID or custom string.",
    )

class EventResponse(BaseModel):

    id: UUID
    event_type: str
    recipient: str
    payload: Dict[str, Any]
    status: EventStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EventCreateResponse(BaseModel):
    id: UUID
    status: EventStatus
    message: str = "Event created and queued for processing"

    class Config:
        from_attributes = True


class DLQReplayRequest(BaseModel):

    recipient: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Override recipient for the replayed event",
    )

    payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Override payload for the replayed event",
    )


class FailedEventResponse(BaseModel):

    id: UUID
    event_id: UUID
    event_type: str
    recipient: str
    payload: Dict[str, Any]
    error_message: str
    error_traceback: Optional[str]
    retry_count: int
    max_retries: int
    last_error_at: Optional[datetime]
    replayed_at: Optional[datetime]
    replay_event_id: Optional[UUID]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

        