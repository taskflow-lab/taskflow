from flask import Blueprint, jsonify

from app.modules.health import services

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    return jsonify({"status": "ok", **services.get_app_info()}), 200


@bp.get("/ready")
def ready():
    checks = services.run_readiness_checks()
    is_ready = all(check["ok"] for check in checks.values())
    return jsonify({"status": "ready" if is_ready else "not_ready", "checks": checks}), (200 if is_ready else 503)
