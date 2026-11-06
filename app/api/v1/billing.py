from flask import g, jsonify

from app.api.v1 import api_login_required, api_v1_bp, get_json_body
from app.modules.billing import services


@api_v1_bp.get("/billing/plans")
def list_plans():
    return jsonify({"plans": services.list_plans()}), 200


@api_v1_bp.get("/billing/subscription")
@api_login_required
def get_subscription():
    subscription = services.get_subscription(g.api_user)
    return jsonify({"subscription": subscription.to_dict()}), 200


@api_v1_bp.post("/billing/subscription")
@api_login_required
def change_subscription():
    data = get_json_body()
    subscription, payment = services.change_plan(g.api_user, data.get("plan", ""))
    return jsonify({
        "subscription": subscription.to_dict(),
        "payment": payment.to_dict() if payment else None,
    }), 200


@api_v1_bp.get("/billing/usage")
@api_login_required
def get_usage():
    return jsonify({"usage": services.get_usage(g.api_user)}), 200
