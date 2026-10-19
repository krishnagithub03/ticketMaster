from password_validator import PasswordValidator
from flask import jsonify
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
    return jsonify({"is_valid": is_valid, "errors": errors})