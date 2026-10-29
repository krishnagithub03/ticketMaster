from enum import Enum
import secrets
from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy import CheckConstraint, UniqueConstraint

class EventSeatInventoryStatus(Enum):
    BOOKED = "booked"
    HELD = "held"
    AVAILABLE = "available"
    BLOCKED = "blocked"

class EventSeatInventory(db.Model):
    __tablename__ = "event_seat_inventories"

    # Public identifier: inv_ followed by random hexadecimal characters.
    id = db.Column(
        db.String(32),
        primary_key=True,
        default=lambda: "inv_" + secrets.token_hex(6)
    )

    event_occurrence_id = db.Column(
        db.String(32),
        db.ForeignKey("event_occurrences.id"),
        nullable=False
    )
    seat_id = db.Column(
        db.String(32),
        db.ForeignKey("seats.id"),
        nullable=False
    )
    status = db.Column(
        db.Enum(EventSeatInventoryStatus, name="event_seat_inventory_status"),
        default=EventSeatInventoryStatus.AVAILABLE,
        nullable=False
    )
    price = db.Column(
        db.Numeric(precision=10, scale=2),
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
        db.CheckConstraint('price >= 0', name='check_non_negative_price'),
        db.UniqueConstraint('event_occurrence_id', 'seat_id', name='uq_event_occurrence_seat'),
    )
    event_occurrence = db.relationship(
    "EventOccurrence",
    back_populates="seat_inventories"
    )
    seat = db.relationship(
    "Seat",
    back_populates="event_inventories"
    )
    booking_seats = db.relationship(
    "BookingSeat",
    back_populates="event_seat_inventory"
    )