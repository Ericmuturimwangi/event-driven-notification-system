from sqlalchemy import Column, String, JSON, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from enum import Enum
from uuid import uuid4
from datetime import datetime
from app.db.base import Base

class EventStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Event(Base):

    __tablename__ = "events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    event_type = Column(
        String(50),
        nullable=False,
        index=True,
    )

    recipient = Column(
        String(255),
        nullable=False,
        index=True
    )
    
    payload =Column(
        JSON, 
        nullable=False,
        default=dict,
    )

    status =Column(
        SQLEnum(EventStatus),
        nullable = False,
        default=EventStatus.PENDING,
        index=True,
    )

    created_at = Column(
        DateTime,
        nullable =False,
        default = datetime.utcnow,
        server_default = func.now(),
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default = func.now(),
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, type={self.event_type}, status={self.status})>"

