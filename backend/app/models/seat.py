from enum import Enum
import secrets
from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy import CheckConstraint, UniqueConstraint

class SeatType(Enum):
    STANDARD = "standard"
    VIP = "vip"
    RECLINER = "recliner"

class Seat(db.Model):
    __tablename__ = "seats"

    # Public identifier: seat_ followed by random hexadecimal characters.
    id = db.Column(
        db.String(32),
        primary_key=True,
        default=lambda: "seat_" + secrets.token_hex(6)
    )

    venue_hall_id = db.Column(
        db.String(32),
        db.ForeignKey("venue_halls.id"),
        nullable=False
    )
    # should be in uppercase only
    row_label = db.Column(
        db.String(5),
        nullable=False
    )
    seat_number = db.Column(
        db.Integer(),
        nullable=False
    )
    seat_type = db.Column(
        db.Enum(SeatType, name="seat_type"),
        default=SeatType.STANDARD,
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
        db.CheckConstraint('seat_number > 0', name='check_positive_seat_number'),
        db.UniqueConstraint('venue_hall_id', 'row_label', 'seat_number', name='uq_venue_hall_seat'),
    )
    venue_hall = db.relationship(
    "VenueHall",
    back_populates="seats"
    )
    event_inventories = db.relationship(
    "EventSeatInventory",
    back_populates="seat"
    )
