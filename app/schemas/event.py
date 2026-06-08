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
        from_attributed =True
