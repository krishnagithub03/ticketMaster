from app.extensions import redis_client
from app.models.user import User
from app.extensions import db

def is_token_revoked(jwt_payload):
    jti = jwt_payload["jti"]
    key = f"revoked_token:{jti}"
    entry = redis_client.get(key)
    if entry is not None:
        return True 
    user_id = jwt_payload["sub"]
    user = db.session.get(User,user_id)  # Ensure the user exists
    if user is None:
        return True 
    # compare the token version in the payload with the user's current token version
    if jwt_payload.get("token_version") != user.token_version:
        return True  # Token is revoked if versions don't match
     
    return False  # Token is not revoked
