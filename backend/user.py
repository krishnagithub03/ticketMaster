from flask import Flask, request, jsonify
from flask_cors import CORS 
import os
import random
from password_validator import PasswordValidator
import json
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import uuid
from datetime import datetime, date


app = Flask(__name__)
CORS(app)
load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define a Database Model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def health_check():
    return 'Service is up an running'

schema = PasswordValidator()
schema.min(8).max(100).has().uppercase().has().lowercase().has().digits().has().symbols()

def check_password(password):
    rules = {
        "minimum length (8)": len(password) >= 8,
        "maximum length (100)": len(password) <= 100,
        "uppercase letter": any(character.isupper() for character in password),
        "lowercase letter": any(character.islower() for character in password),
        "digit": any(character.isdigit() for character in password),
        "symbol": any(not character.isalnum() for character in password),
    }
    is_valid = schema.validate(password)
    errors = [rule for rule, passed in rules.items() if not passed]
    return {"is_valid": is_valid, "errors": errors}

@app.route('/user/register',methods=['POST'])
def user_register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing or invalid JSON body"}), 400
        
    defaultName = "User" + str(random.randint(1,1000))
    name = data.get("name", defaultName)
    email = data.get("email")
    password = data.get("password")
    if email is None:
        return 'Email is required'
    if password is None:
        return 'password is required'
    password_status = check_password(password=password)
    if not password_status.get("is_valid"):
        res = {
            "message" : f"password is not strong, check failed rules: {password_status.get('errors')}"
        }
        return json.dumps(res)

    # save the user in db 

    new_user = User(
        name=name,
        email=email,
        password=password
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify(new_user.to_dict()), 201
        
    except Exception as e:
        # Roll back the database transaction if something goes wrong (e.g., duplicate username)
        db.session.rollback()
        return jsonify({"error": "User could not be created. Username or email might already exist."}), 400


@app.route('/user/login', methods=['POST'])
def user_login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing or invalid JSON body"}), 400

    email = data.get("email")
    password = data.get("password")
    
    if email is None or password is None:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email, password=password).first()
    # when the user logs into this set some cookies like refresh and access tokens 
    access_token = uuid.getnode(4)
    curr_status = True if user.get('last_login') < datetime-60 else False
    data = {
        "user" : {
            "id" : user.get('id'),
            "name" : user.get('name'),
            "email" : user.get('emial'),
            "status" : "active" if curr_status is True else "not active"
        },
        "authorization" : {
            "access_token" : access_token, 
             "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "Bearer",
            "expires_in": 900,
            "permissions": ["admin"],
        },
        "meta" : {
            "last_login" : datetime,
        }

    }
    if user:
        return jsonify(user.get_all()), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401

if __name__ == '__main__':
    app.run(debug=True)