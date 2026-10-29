import secrets
from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy import CheckConstraint

class Venue(db.Model):
    __tablename__ = "venues"

    # Public identifier: ven_ followed by random hexadecimal characters.
    id = db.Column(
        db.String(32),
        primary_key=True,
        default=lambda: "ven_" + secrets.token_hex(6)
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )
    description = db.Column(
        db.Text(),
        nullable=True
    )
    address_line = db.Column(
        db.String(200),
        nullable=False
    )
    city = db.Column(
        db.String(100),
        nullable=False
    )
    state = db.Column(
        db.String(100),
        nullable=False
    )
    country = db.Column(
        db.String(100),
        nullable=False
    )
    postal_code = db.Column(
        db.String(20),
        nullable=False
    )
    
    latitude = db.Column(
        db.Float(),
        nullable=True,
    )
    longitude = db.Column(
        db.Float(),
        nullable=True,
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
    #Add a database constraint to ensure latitude is between -90 and 90 and longitude is between -180 and 180 when provided.
    __table_args__ = (
        CheckConstraint('latitude IS NULL OR (latitude >= -90 AND latitude <= 90)', name='check_latitude_range'),
        CheckConstraint('longitude IS NULL OR (longitude >= -180 AND longitude <= 180)', name='check_longitude_range'),
    )
    halls = db.relationship(
    "VenueHall",
    back_populates="venue"
    )
