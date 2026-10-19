import re

def validate_email(email):
    # Basic email format validation using regex
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return False, "Invalid email format"
    
    # Additional checks can be added here (e.g., domain validation)
    
    return True, "Valid email"