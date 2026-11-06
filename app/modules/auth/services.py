import re

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.extensions import db
from app.modules.auth.models import ROLES, User

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
TOKEN_SALT = "taskflow-api-token"


def normalize_email(email):
    return (email or "").strip().lower()


def validate_registration(email, name, password):
    errors = {}
    if not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address"
    if not name:
        errors["name"] = "Name is required"
    elif len(name) > 120:
        errors["name"] = "Name must be 120 characters or fewer"
    if len(password or "") < MIN_PASSWORD_LENGTH:
        errors["password"] = f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    return errors


def get_user_by_email(email):
    return User.query.filter_by(email=normalize_email(email)).first()


def register_user(email, name, password, role="member"):
    email = normalize_email(email)
    name = (name or "").strip()

    errors = validate_registration(email, name, password)
    if errors:
        raise ValueError(next(iter(errors.values())))
    if role not in ROLES:
        raise ValueError(f"Role must be one of: {', '.join(ROLES)}")
    if get_user_by_email(email):
        raise ValueError("An account with this email already exists")

    user = User(email=email, name=name, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate(email, password):
    user = get_user_by_email(email)
    if user and password and user.check_password(password):
        return user
    return None


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=TOKEN_SALT)


def generate_api_token(user):
    return _serializer().dumps({"uid": user.id})


def get_user_by_token(token):
    if not token:
        return None
    try:
        data = _serializer().loads(token, max_age=current_app.config["API_TOKEN_MAX_AGE_SECONDS"])
    except (BadSignature, SignatureExpired):
        return None
    return db.session.get(User, data.get("uid"))
