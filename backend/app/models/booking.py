from enum import Enum
import secrets
from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy import CheckConstraint

class BookingStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class Booking(db.Model):
    __tablename__ = "bookings"

    # Public identifier: bkg_ followed by random hexadecimal characters.
    id = db.Column(
        db.String(32),
        primary_key=True,
        default=lambda: "bkg_" + secrets.token_hex(6)
    )
    user_id = db.Column(
        db.String(32),
        db.ForeignKey("users.id"),
        nullable=False
    )
    event_occurrence_id = db.Column(
        db.String(32),
        db.ForeignKey("event_occurrences.id"),
        nullable=False
    )
    booking_reference = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )
    status = db.Column(
        db.Enum(BookingStatus, name="booking_status"),
        default=BookingStatus.PENDING,
        nullable=False
    )
    total_amount = db.Column(
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
        db.CheckConstraint('total_amount >= 0', name='check_non_negative_total_amount'),
    )
    user = db.relationship("User", back_populates="bookings")
    booking_seats = db.relationship(
    "BookingSeat",
    back_populates="booking"
    )
    payments = db.relationship(
    "Payment",
    back_populates="booking"
    )

   