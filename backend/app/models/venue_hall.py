import secrets
from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy import CheckConstraint, UniqueConstraint


class VenueHall(db.Model):
    __tablename__ = "venue_halls"

    # Public identifier: hall_ followed by random hexadecimal characters.
    id = db.Column(
        db.String(32),
        primary_key=True,
        default=lambda: "hall_" + secrets.token_hex(6)
    )
    venue_id = db.Column(
        db.String(32),
        db.ForeignKey("venues.id"),
        nullable=False
    )
    name = db.Column(
        db.String(100),
        nullable=False
    )
    capacity = db.Column(
        db.Integer(),
        nullable=False
    )
    hall_type = db.Column(
        db.String(50),
        nullable=True
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
    # Prevent duplicate hall names within the same venue using a unique constraint on (venue_id, name).
    __table_args__ = (
        db.CheckConstraint('capacity > 0', name='check_positive_capacity'),
        db.UniqueConstraint('venue_id', 'name', name='uq_venue_hall_name')
    )
    venue = db.relationship(
    "Venue",
    back_populates="halls"
    )
    seats = db.relationship(
    "Seat",
    back_populates="venue_hall"
    )