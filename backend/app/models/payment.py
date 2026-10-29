from enum import Enum
import secrets
from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy import CheckConstraint

class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"

class Payment(db.Model):
    __tablename__ = "payments"

    # Public identifier: pay_ followed by random hexadecimal characters.
    id = db.Column(
        db.String(32),
        primary_key=True,
        default=lambda: "pay_" + secrets.token_hex(6)
    )
    booking_id = db.Column(
        db.String(32),
        db.ForeignKey("bookings.id"),
        nullable=False
    )
    amount = db.Column(
        db.Numeric(precision=10, scale=2),
        nullable=False
    )
    status = db.Column(
        db.Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.PENDING,
        nullable=False
    )
    provider = db.Column(
        db.String(50),
        nullable=False
    )
    provider_payment_id = db.Column(
        db.String(100),
        unique=True,
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
    __table_args__ = (
        db.CheckConstraint('amount >= 0', name='check_non_negative_amount'),
    )
    booking = db.relationship(
    "Booking",
    back_populates="payments"
    )