from functools import wraps

from flask import Blueprint, g, jsonify, request
from flask_login import current_user
from werkzeug.exceptions import HTTPException

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


def error_response(status, message, details=None):
    body = {"error": {"status": status, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def get_json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")
    return data


def api_login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        from app.modules.auth.services import get_user_by_token

        user = None
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            user = get_user_by_token(header[len("Bearer "):].strip())
        elif current_user.is_authenticated:
            user = current_user._get_current_object()

        if user is None:
            return error_response(401, "Authentication required")

        g.api_user = user
        return view(*args, **kwargs)

    return wrapper


@api_v1_bp.errorhandler(ValueError)
def handle_value_error(error):
    return error_response(400, str(error))


@api_v1_bp.errorhandler(LookupError)
def handle_lookup_error(error):
    message = error.args[0] if error.args else "Not found"
    return error_response(404, message)


@api_v1_bp.errorhandler(PermissionError)
def handle_permission_error(error):
    status = getattr(error, "status_code", 403)
    return error_response(status, str(error) or "Forbidden")


@api_v1_bp.errorhandler(HTTPException)
def handle_http_error(error):
    return error_response(error.code, error.description)


from app.api.v1 import auth, billing, health, issues, projects  # noqa: E402,F401
