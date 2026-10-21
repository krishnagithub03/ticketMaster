from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_redis import FlaskRedis

# Extensions are created here but not bound to an app yet.
db = SQLAlchemy()

# TODO 1: Create the migration extension.
migrate = Migrate()
# TODO 2: Create the JWT extension.
jwt = JWTManager()

mail = Mail()

redis_client = FlaskRedis()