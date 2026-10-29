from enum import Enum
import secrets
from datetime import datetime, timezone
from app.extensions import db

class EventStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"

class Event(db.Model):
    __tablename__ = "events"

    # Public identifier: evt_ followed by random hexadecimal characters.
    id = db.Column(
        db.String(32),
        primary_key=True,
        default=lambda: "evt_" + secrets.token_hex(6)
    )

    title = db.Column(
        db.String(100),
        nullable=False
    )
    description = db.Column(
        db.Text(),
        nullable=True
    )
    category = db.Column(
        db.String(50),
        nullable=False
    )
    image_url = db.Column(
        db.Text(),
        nullable=True
    )
    status = db.Column(
        db.Enum(EventStatus, name="event_status"),
        default=EventStatus.DRAFT,
        nullable=False
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    occurrences = db.relationship(
    "EventOccurrence",
    back_populates="event"
    )