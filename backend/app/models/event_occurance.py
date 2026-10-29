from enum import Enum
import secrets
from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy import CheckConstraint

class EventOccurrenceStatus(Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class EventOccurrence(db.Model):
    __tablename__ = "event_occurrences"

    # Public identifier: occ_ followed by random hexadecimal characters.
    id = db.Column(
        db.String(32),
        primary_key=True,
        default=lambda: "occ_" + secrets.token_hex(6)
    )

    event_id = db.Column(
        db.String(32),
        db.ForeignKey("events.id"),
        nullable=False
    )
    venue_hall_id = db.Column(
        db.String(32),
        db.ForeignKey("venue_halls.id"),
        nullable=False
    )
    starts_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )
    # validation: Ensure that ends_at is after starts_at. This can be done in the application logic or with a database constraint.
    ends_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )
    status = db.Column(
        db.Enum(EventOccurrenceStatus, name="event_occurrence_status"),
        default=EventOccurrenceStatus.SCHEDULED,
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
    __table_args__ = (
        CheckConstraint('ends_at > starts_at', name='check_ends_after_starts'),
    )
    event = db.relationship(
    "Event",
    back_populates="occurrences"
    )
    seat_inventories = db.relationship(
    "EventSeatInventory",
    back_populates="event_occurrence"
    )