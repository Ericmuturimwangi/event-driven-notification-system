from sqlalchemy import Column, String, JSON, DateTime, Text, Integer, Enum as SQLEnum
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

    idempotency_key = Column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
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


class FailedEvent(Base):

    __tablename__ = "failed_events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    event_id = Column(
        UUID(as_uuid=True),
        nullable=False,
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
    )

    payload = Column(
        JSON, 
        nullable=False,
        default=dict,
    )

    error_message = Column(
        Text,
        nullable=False,
    )

    error_traceback = Column(
        Text,
        nullable=True,
    )

    retry_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    max_retries = Column(
        Integer,
        nullable=False,
        default=3,
    )

    last_error_at= Column(
        DateTime,
        nullable=True,
    )

    replayed_at = Column(
        DateTime,
        nullable=True,
    )

    replay_event_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    resolved_at = Column(
        DateTime,
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<FailedEvent(event_id={self.event_id}, type={self.event_type}, retries={self.retry_count})>"

        