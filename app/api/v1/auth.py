from flask import g, jsonify

from app.api.v1 import api_login_required, api_v1_bp, error_response, get_json_body
from app.modules.auth import services


@api_v1_bp.post("/auth/register")
def register():
    data = get_json_body()
    user = services.register_user(
        email=data.get("email", ""),
        name=data.get("name", ""),
        password=data.get("password", ""),
    )
    token = services.generate_api_token(user)
    return jsonify({"user": user.to_dict(), "token": token}), 201


@api_v1_bp.post("/auth/token")
def get_token():
    data = get_json_body()
    user = services.authenticate(data.get("email", ""), data.get("password", ""))
    if user is None:
        return error_response(401, "Invalid email or password")
    token = services.generate_api_token(user)
    return jsonify({"user": user.to_dict(), "token": token}), 200


@api_v1_bp.get("/auth/me")
@api_login_required
def me():
    return jsonify({"user": g.api_user.to_dict()}), 200
