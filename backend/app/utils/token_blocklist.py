from app.extensions import redis_client

def is_token_revoked(jwt_payload):
    jti = jwt_payload["jti"]
    key = f"revoked_token:{jti}"
    entry = redis_client.get(key)
    return entry is not None