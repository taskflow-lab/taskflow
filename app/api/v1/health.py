from flask import jsonify

from app.api.v1 import api_v1_bp
from app.modules.health import services


@api_v1_bp.get("/health")
def health():
    return jsonify({"status": "ok", **services.get_app_info()}), 200


@api_v1_bp.get("/ready")
def ready():
    checks = services.run_readiness_checks()
    is_ready = all(check["ok"] for check in checks.values())
    status_code = 200 if is_ready else 503
    return jsonify({"status": "ready" if is_ready else "not_ready", "checks": checks}), status_code
