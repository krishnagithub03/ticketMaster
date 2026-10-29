import secrets
from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy import CheckConstraint


class BookingSeat(db.Model):
    __tablename__ = "booking_seats"

    # Public identifier: bks_ followed by random hexadecimal characters.
    id = db.Column(
        db.String(32),
        primary_key=True,
        default=lambda: "bks_" + secrets.token_hex(6)
    )
    booking_id = db.Column(
        db.String(32),
        db.ForeignKey("bookings.id"),
        nullable=False
    )
    event_seat_inventory_id = db.Column(
        db.String(32),
        db.ForeignKey("event_seat_inventories.id"),
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
        db.UniqueConstraint('booking_id', 'event_seat_inventory_id', name='unique_booking_seat')
    )
    booking = db.relationship(
    "Booking",
    back_populates="booking_seats"
    )
    event_seat_inventory = db.relationship(
    "EventSeatInventory",
    back_populates="booking_seats"
    )