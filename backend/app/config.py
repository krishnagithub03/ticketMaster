import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def env_bool(name, default):
    value = os.getenv(name, str(default)).strip().lower()

    if value not in ("true", "false"):
        raise RuntimeError(f"{name} must be 'true' or 'false'")

    return value == "true"


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("DATABASE_URI environment variable is required.")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY environment variable is required.")

    JWT_TOKEN_LOCATION = ["headers", "cookies"]

    JWT_ACCESS_COOKIE_NAME = "access_token_cookie"
    JWT_REFRESH_COOKIE_NAME = "refresh_token_cookie"

    JWT_COOKIE_SECURE = True
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = "Lax"

    JWT_COOKIE_CSRF_PROTECT = True

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    FRONTEND_ORIGIN = os.getenv(
        "FRONTEND_ORIGIN", "http://localhost:3000"
    )

    # SMTP configuration
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")

    try:
        MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    except ValueError:
        raise RuntimeError("MAIL_PORT must be an integer.")

    MAIL_USE_TLS = env_bool("MAIL_USE_TLS", True)
    MAIL_USE_SSL = env_bool("MAIL_USE_SSL", False)

    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    if not MAIL_USERNAME:
        raise RuntimeError("MAIL_USERNAME environment variable is required.")

    if not MAIL_PASSWORD:
        raise RuntimeError("MAIL_PASSWORD environment variable is required.")

    if not MAIL_DEFAULT_SENDER:
        raise RuntimeError(
            "MAIL_DEFAULT_SENDER environment variable is required."
        )

    if MAIL_USE_TLS and MAIL_USE_SSL:
        raise RuntimeError("Enable either TLS or SSL, not both.")

    REDIS_URL = os.getenv("REDIS_URL")
