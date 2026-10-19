from flask import Blueprint, json, request, jsonify
from app.extensions import db
from app.models import User, AccountStatus, UserRole
from app.utils.security import hash_password
from app.utils.passwordStrength import check_password
from app.utils.emailValidator import validate_email

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
    if not password.strip():
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
    # 5. Create and save the user
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=password_hash,
        avatar_url=avatar_url,
        status=AccountStatus.PENDING_VERIFICATION,
        role=UserRole.CUSTOMER
    )
    db.session.add(new_user)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message" : "An error occurred while creating the user. Please try again."}), 500
    # 6. Return the response
    return jsonify({"message" : "User added successfully!"}), 201