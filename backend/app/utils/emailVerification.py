import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from flask import jsonify

def generate_verification_token():
    token = secrets.token_urlsafe(64)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return token,token_hash

def get_token_expiration():
    current_time = datetime.now(timezone.utc)
    exp_time = current_time + timedelta(minutes=15)
    return exp_time
