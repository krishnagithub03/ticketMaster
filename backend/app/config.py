import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError(
            "CRITICAL ERROR: 'DATABASE_URI' environment variable is not set or empty. "
            "The application cannot start without a secure DB key."
        )

    # TODO 3: Disable SQLAlchemy modification tracking.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # TODO 4: Load JWT_SECRET_KEY from the environment.
    # Do not silently fall back to a predictable secret.
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        raise RuntimeError(
        "CRITICAL ERROR: 'JWT_SECRET_KEY' environment variable is not set or empty. "
        "The application cannot start without a secure secret key."
        )
    # TODO 5: Set access-token lifetime to 15 minutes.
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=15)

    # TODO 6: Choose a refresh-token lifetime.
    # For this project, consider a duration of several days.
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=7)

    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN")

