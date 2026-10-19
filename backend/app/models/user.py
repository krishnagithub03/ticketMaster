from enum import Enum
import secrets
from datetime import datetime, timezone
from app.extensions import db

class UserRole(Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"

# TODO 1: Define an AccountStatus enum.
# Include pending verification, active, and suspended.
class AccountStatus(Enum):
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    SUSPENDED = "suspended"

class User(db.Model):
    __tablename__ = "users"

    # Public identifier: usr_ followed by random hexadecimal characters.
    id = db.Column(
        db.String(32),
        primary_key=True,
        default=lambda: "usr_" + secrets.token_hex(6)
    )

    # TODO 2: Add first_name and last_name.
    # Both should be required strings with reasonable length limits.
    first_name = db.Column(
        db.String(32),
        nullable=False
    )
    last_name = db.Column(
        db.String(32),
        nullable=False
    )

    # TODO 3: Add email.
    # It must be unique, required, and indexed appropriately.
    email= db.Column(
        db.String(254),
        unique=True,
        nullable=False
    )

    # TODO 4: Add password_hash.
    # Never store the original password.
    password_hash = db.Column(
        db.String(256),
        nullable=False
    )

    avatar_url = db.Column(
        db.Text(),
        nullable=True
    )
    status = db.Column(
        db.Enum(AccountStatus), 
        default=AccountStatus.PENDING_VERIFICATION, 
        nullable=False
    )
    role = db.Column(
        db.Enum(UserRole), 
        default=UserRole.CUSTOMER, 
        nullable=False
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    last_login_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )
    email_verified_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )
