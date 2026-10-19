from werkzeug.security import generate_password_hash, check_password_hash

# returns the hashed password for plain passowrd
def hash_password(password):
    return generate_password_hash(password=password,method="scrypt",salt_length=16)

# check provided password with stored password hash
def verify_password(password,password_hash):
    return check_password_hash(pwhash=password_hash, password=password)


if __name__ =='__main__':
    hashed = hash_password("MyStrongPassword123!")
    print(hashed != "MyStrongPassword123!")  # True
    print(verify_password("MyStrongPassword123!", hashed))  # True
    print(verify_password("WrongPassword", hashed))  # False
