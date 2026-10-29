from flask import Blueprint, json, request, jsonify
from app.extensions import db
from app.models import User, AccountStatus, UserRole
from app.utils.security import hash_password, verify_password
from app.utils.passwordStrength import check_password
from app.utils.emailValidator import validate_email
import hashlib
import math
from app.utils.emailVerification import generate_verification_token, get_token_expiration
from datetime import datetime, timezone
from app.utils.emailSender import send_password_reset_email, send_verification_email
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import (create_access_token, 
create_refresh_token, 
jwt_required, 
get_jwt_identity, 
set_refresh_cookies,
unset_refresh_cookies,
get_jwt
)
from app.extensions import redis_client
from app.utils.token_blocklist import is_token_revoked

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    # 1. Read and validate request JSON
    request_data = request.get_json()

    # 2. Validate required fields
    if not request_data:
        return jsonify({"message" : "No input data is provided, please provide required fields"}), 400
    first_name = request_data.get('first_name')
    last_name = request_data.get('last_name')
    email = request_data.get('email')
    password = request_data.get('password')
    avatar_url = request_data.get('avatar_url')

    if not isinstance(first_name, str):
            return jsonify({"message" : "First name must be a string"}), 400
    first_name = first_name.strip()
    if not first_name:
        return jsonify({"message" : "No first name data is provided, please provide required fields"}), 400
    
    if not isinstance(last_name, str):
            return jsonify({"message" : "Last name must be a string"}), 400
    last_name = last_name.strip()
    if not last_name:
        return jsonify({"message" : "No last name data is provided, please provide required fields"}), 400
    
    if not email:
        return jsonify({"message" : "No email data is provided, please provide required fields"}), 400
    else:
        # validate email is a string
        if not isinstance(email, str):
            return jsonify({"message" : "Email must be a string"}), 400
        email = email.strip().lower()
        # Validate email format
        is_valid_email, email_message = validate_email(email)
        if not is_valid_email:
            return jsonify({"message" : email_message}), 400
    if not password:
        return jsonify({"message" : "No password data is provided, please provide required fields"}), 400
    else:
        # validate password is a string 
        if not isinstance(password, str):
            return jsonify({"message" : "Password must be a string"}), 400
        # Validate password strength
        password_status = check_password(password=password)
        password_status_json = password_status.get_json()
        if not password_status_json['is_valid']:
            res = {
                "message" : f"password is not strong, check failed rules: {password_status_json['errors']}"
            }
            return jsonify(res), 400
    
    # 3. Normalize email and check if it already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message" : "Email already exists, please use a different email or try logging in"}), 409
    # 4. Hash the password
    password_hash = hash_password(password)

    token,token_hash = generate_verification_token()
    email_token_ttl = get_token_expiration()
  
    # 5. Create and save the user
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=password_hash,
        avatar_url=avatar_url,
        status=AccountStatus.PENDING_VERIFICATION,
        role=UserRole.CUSTOMER,
        email_verification_token_hash=token_hash,
        email_verification_expires_at=email_token_ttl
    )
    db.session.add(new_user)
    try:
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        db.session.rollback()
        return jsonify({"message" : "Email already exists, please use a different email or try logging in"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"message" : "An error occurred while creating the user. Please try again."}), 500

    try:
        send_verification_email(email,token)
    except Exception:
    # Do NOT roll back the committed user.
    # The account remains pending verification.
        return jsonify({
        "message": (
            "Your account was created, but we couldn't send "
            "the verification email. Please try again later."
        ),
        "data": {
            "email": email,
            "status": AccountStatus.PENDING_VERIFICATION.value
        }
        }), 503
    # 6. Return the response
    return jsonify({
    "message": "Account created. Please check your email to verify your account.",
    "data": {
        "email": email,
        "status": AccountStatus.PENDING_VERIFICATION.value
    }
    }), 201

@auth_bp.route("/verify-email", methods=["GET"])
def verify_email():
    token = request.args.get('token')
    if not token:
        return jsonify({"message" : "no token is provided"}), 400
    #hash the token 
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    # Find the user with the matching token hash
    user = User.query.filter_by(email_verification_token_hash=token_hash).first()

    if not user:
        return jsonify({"message" : "Invalid or expired token provided"}), 400
    
    if user.status == AccountStatus.SUSPENDED:
        return jsonify({"message" : "User's account is suspended, contact admin"}), 401
    if user.status == AccountStatus.ACTIVE:
        return jsonify({"message" : "User's account is already active, email verified"}), 200
    current_time = datetime.now(timezone.utc)

    if (user.email_verification_expires_at is None or current_time >= user.email_verification_expires_at):
        return jsonify({"message" : "token expired, try again"}), 400

    if user.status != AccountStatus.PENDING_VERIFICATION:
        return jsonify({"message" : "Account status invalid, contact admin"}), 400
    
    user.status = AccountStatus.ACTIVE
    user.email_verified_at = current_time
    user.email_verification_expires_at = None
    user.email_verification_token_hash = None

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message" : "An error occurred while verifying email. Please try again."}), 500

    return jsonify({"message" : "email verified successfully"}), 200

@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    # 1. Read and validate the email
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"message": "Invalid request body"}), 400
    email = body.get("email")
    if not isinstance(email, str) or not email.strip():
        return jsonify({"message": "A valid email is required"}), 400
    email = email.strip().lower()
    if not email:
        return jsonify({"message" : "email not provided, please provide one"}), 400
    is_valid_email, email_message = validate_email(email)
    if not is_valid_email:
        return jsonify({"message" : email_message}), 400
    # 2. Find the user
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message" : "account not found with provided email, try with another email"}), 400
    # 3. Check the account status
    if user.status == AccountStatus.ACTIVE:
        return jsonify({"message" : "account already active, no verification required"}), 400
    if user.status == AccountStatus.SUSPENDED:
        return jsonify({"message" : "account suspended, contact admin"}), 400
    # 4. Generate a new token and expiration
    token,token_hash = generate_verification_token()
    # 5. Save the new token hash
    user.email_verification_token_hash = token_hash
    token_ttl = get_token_expiration()
    user.email_verification_expires_at = token_ttl

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message" : "unable to save new token, please try again later"}), 500
    
    # 6. Send the verification email
    try:
        send_verification_email(email,token)
    except Exception as e:
        return jsonify({"message": "unable to send email, please try again later"}), 503
    return jsonify({"message" : "email resent successfully for verification"}),200

@auth_bp.route("/login", methods=["POST"])
def login():
    # 1. Read and validate email and password
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"message": "Invalid request body"}), 400
    email = body.get("email")
    if not isinstance(email, str) or not email.strip():
        return jsonify({"message": "A valid email is required"}), 400
    email = email.strip().lower()
    if not email:
        return jsonify({"message" : "email not provided, please provide one"}), 400
    is_valid_email, email_message = validate_email(email)
    if not is_valid_email:
        return jsonify({"message" : email_message}), 401
    password = body.get("password")
    if not isinstance(password, str) or not password.strip():
        return jsonify({"message": "A valid password is required"}), 400
    if not password:
        return jsonify({"message" : "password not provided, please provide one"}), 400
    # 2. Find the user by normalized email
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message" : "Invalid email or password"}), 401
    # 3. Verify the password
    user_password_hash_in_db = user.password_hash
    if not verify_password(password=password,password_hash=user_password_hash_in_db):
        return jsonify({"message" : "Incorrect password, please provide the correct password"}), 401
    # 4. Reject non-active accounts
    if user.status != AccountStatus.ACTIVE:
        return jsonify({"message" : "Account inactive, please verify the email to login"}), 401
    # 5. Update last_login_at
    user.last_login_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message" : "Unable to login, please try again later"}), 500
    # 6. Generate access and refresh tokens
    access_token = create_access_token(identity=user.id, additional_claims={"token_version" : user.token_version})
    refresh_token = create_refresh_token(identity=user.id, additional_claims={"token_version" : user.token_version})
    # 7. Return the response

    response = {
        "status" : "success",
        "message" : f'Logged in as {email}',
        "data" : {
            "user" : {
                "id" : user.id,
                "first_name" : user.first_name,
                "last_name" : user.last_name,
                "email" : user.email,
                "avatar_url" : user.avatar_url,
                "status" : user.status.value,
            },
            "authorization" : {
                "access_token" : access_token,
                "token_type" : "Bearer",
                "expires_in" : 15 * 60,  # 15 minutes in seconds
                "role" : user.role.value,
                "permissions" : []
            },
            "meta" : {
                "last_login_at" : user.last_login_at.isoformat() if user.last_login_at else None,
                "locale" : "en-US",
                "timezone" : "UTC"
            }
        }
    }
    flask_response = jsonify(response)
    set_refresh_cookies(flask_response,refresh_token)
    return flask_response, 200

@auth_bp.route("/refresh", methods=["POST"]) 
@jwt_required(refresh=True, locations=["cookies"])
def refresh_access_token():
    # 1. Require a valid refresh token from cookies
    # 2. Extract the user ID from the token
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"message": "Invalid refresh token"}), 401
    # 3. Find the user and check account status
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}), 401
    if user.status != AccountStatus.ACTIVE:
        return jsonify({"message": "Account inactive, please verify the email to login"}), 401
    # 4. Generate a new access token
    access_token = create_access_token(identity=user.id)
    # 5. Return the response
    response = {
        "status": "success",
        "message": "Access token refreshed",
        "data": {
            "authorization": {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": 15 * 60,  # 15 minutes in seconds
                "role": user.role.value,
                "permissions": []
            }
        }
    }
    return jsonify(response), 200

@auth_bp.route("/logout", methods=["POST"])
@jwt_required(refresh=True, locations=["cookies"])
def logout():
    # 1. Validate the refresh token from cookies
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"message": "Invalid refresh token"}), 401
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}), 401
    # 2. Prepare a successful response
    response = jsonify({"message": "Logged out successfully"})
    # 3. Clear the refresh and CSRF cookies
    #TOKEN REVOKED: The refresh token will be revoked automatically by the token blocklist mechanism.
    # Add the refresh token to the blocklist
    jwt_payload = get_jwt()
    jti = jwt_payload['jti']
    remaining_time = max(
        1,
        math.ceil(jwt_payload["exp"] - datetime.now(timezone.utc).timestamp()),
    )
    if jti:
        try:
            redis_client.setex(f"revoked_token:{jti}", remaining_time, "revoked")
        except Exception as e:
            print(f"Error occurred while revoking token: {e}")
    unset_refresh_cookies(response)
    # 4. Return the response
    return response, 200

@auth_bp.route("/me", methods=["GET"])
@jwt_required(locations=["headers"])
def get_current_user():
    # 1. Validate the access token from headers
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"message": "Invalid access token"}), 401
    # 2. Find the user and check account status
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}), 401
    if user.status != AccountStatus.ACTIVE:
        return jsonify({"message": "Account inactive, please verify the email to login"}), 401
    # 3. Return the response with user details
    response = {
        "status": "success",
        "data": {
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "status": user.status.value,
                "role": user.role.value,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            }
        }
    }
    return jsonify(response), 200

@auth_bp.route("/me", methods=["PATCH"])
@jwt_required(locations=["headers"])
def update_current_user():
    # 1. Validate the access token from headers
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"message": "Invalid access token"}), 401
    # 2. Find the user and check account status
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}), 401
    if user.status != AccountStatus.ACTIVE:
        return jsonify({"message": "Account inactive, please verify the email to login"}), 401
    # 3. Read and validate request JSON
    request_data = request.get_json()
    if not request_data or not isinstance(request_data, dict):
        return jsonify({"message": "No input data provided"}), 400
    # 4. Update allowed fields (first_name, last_name, avatar_url)
    allowed_fields = ["first_name", "last_name", "avatar_url"]
    for field in allowed_fields:
        if field in request_data:
            value = request_data[field]
            if isinstance(value, str):
                setattr(user, field, value.strip())
            else:
                return jsonify({"message": f"{field} must be a string"}), 400
    # 5. Commit changes to the database
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while updating the user. Please try again."}), 500
    # 6. Return the response with updated user details
    response = {
        "status": "success",
        "data": {
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "status": user.status.value,
                "role": user.role.value,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            }
        }
    }
    return jsonify(response), 200

@auth_bp.route("/me", methods=["DELETE"])
@jwt_required(locations=["headers"])
def delete_current_user():
    # 1. Validate the access token from headers
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"message": "Invalid access token"}), 401
    # 2. Find the user and check account status
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}), 401
    if user.status != AccountStatus.ACTIVE:
        return jsonify({"message": "Account inactive, please verify the email to login"}), 401
    # 3. Delete the user from the database
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while deleting the user. Please try again."}), 500
    # 4. Return a success response
    return jsonify({"message": "User account deleted successfully"}), 200


@auth_bp.route("/change-password", methods=["PATCH"])
@jwt_required(locations=["headers"])
def change_password():
    # 1. Identify the current user from the access token
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"message": "Invalid access token"}), 401
    # 2. Find the user and check account status
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}), 401
    if user.status != AccountStatus.ACTIVE:
        return jsonify({"message": "Account inactive, please verify the email to login"}), 401
    # 3. Validate current_password and new_password
    request_data = request.get_json()
    if not request_data or not isinstance(request_data, dict):
        return jsonify({"message": "Invalid request data"}), 400
    current_password = request_data.get("current_password")
    new_password = request_data.get("new_password")
    if not current_password or not new_password:
        return jsonify({"message": "Current password and new password are required"}), 400
    # 4. Verify the current password
    if not verify_password(current_password, user.password_hash):
        return jsonify({"message": "Current password is incorrect"}), 401
    # 5. Validate and hash the new password
    password_status = check_password(password=new_password)
    password_status_json = password_status.get_json()
    if not password_status_json['is_valid']:
        return jsonify({"message": f"New password is not strong, check failed rules: {password_status_json['errors']}"}), 400
    # 6. Save the new password
    # check if the new password is same as the current password
    if verify_password(new_password, user.password_hash):
        return jsonify({"message": "New password cannot be the same as the current password"}), 400
    # hash the new password and save it
    user.password_hash = hash_password(new_password)
    user.token_version += 1  # Increment token version to invalidate existing tokens
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while changing the password. Please try again."}), 500
    # 7. Return success
    return jsonify({"message": "Password changed successfully"}), 200

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    # 1. Validate and normalize the email
    request_data = request.get_json()
    if not request_data or not isinstance(request_data, dict):
        return jsonify({"message": "Invalid request data"}), 400
    email = request_data.get("email")
    if not email or not isinstance(email, str):
        return jsonify({"message": "A valid email is required"}), 400
    email = email.strip().lower()
    is_valid_email, email_message = validate_email(email)
    if not is_valid_email:
        return jsonify({"message": email_message}), 400
    # 2. Look up the account
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found"}), 404
    if user.status != AccountStatus.ACTIVE:
        return jsonify({"message": "Account inactive, please verify the email to login"}), 401
    # 3. Generate a secure reset token and store its hash
    token, token_hash = generate_verification_token()
    user.password_reset_token_hash = token_hash
    user.password_reset_expires_at = get_token_expiration()
    # 4. Send the password-reset email
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Unable to save password reset token, please try again later"}), 500
    try:
        send_password_reset_email(email, token)
    except Exception as e:
        return jsonify({"message": "Unable to send password reset email, please try again later"}), 503
    # 5. Return a generic response
    return jsonify({"message": "Password reset email sent."}), 200

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
     # 1. Validate token and new_password
    request_data = request.get_json()
    if not request_data or not isinstance(request_data, dict):
        return jsonify({"message": "Invalid request data"}), 400
    input_token = request_data.get("token")
    if not input_token:
        return jsonify({"message" : "token not found, provide token to change password"}), 400
    if not isinstance(input_token, str) or not input_token.strip():
        return jsonify({"message" : "provide token in valid format"}), 400
    new_password = request_data.get('new_password')
    if not isinstance(new_password,str) or not new_password.strip():
        return jsonify({"message" : "provide password in valid format"}), 400
    password_check =  check_password(new_password).get_json()
    if not password_check.get("is_valid"):
        return jsonify({"message" : f'Password is weak, {password_check.get("errors")}'}), 400
    # 2. Hash the supplied token and find the user
    input_token_hash = hashlib.sha256(input_token.encode("utf-8")).hexdigest()
    user = User.query.filter_by(password_reset_token_hash=input_token_hash).first()
    if not user:
        return jsonify({"message" : "Invalid or expired token provided"}), 400
    # 3. Check token expiration
    current_time = datetime.now(timezone.utc)
    if (user.password_reset_expires_at is None or current_time >= user.password_reset_expires_at):
        return jsonify({"message" : "token expired, try again"}), 400
    # 5. Hash and update the password
    user.password_hash = hash_password(new_password)
    # 6. Clear the reset token fields
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    user.token_version += 1  # Increment token version to invalidate existing tokens
    # 7. Commit and return success
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message" : "An error occurred while resetting the password. Please try again."}), 500
    return jsonify({"message" : "Password reset successfully"}), 200

