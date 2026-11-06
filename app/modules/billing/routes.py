from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.modules.billing import services

bp = Blueprint("billing", __name__, url_prefix="/billing")


@bp.get("/")
@login_required
def plans():
    return render_template(
        "billing/plans.html",
        plans=services.list_plans(),
        usage=services.get_usage(current_user),
    )


@bp.post("/change")
@login_required
def change_plan():
    try:
        subscription, payment = services.change_plan(current_user, request.form.get("plan"))
    except (ValueError, services.PlanLimitError) as error:
        flash(str(error), "danger")
    else:
        message = f"You're now on the {subscription.plan.capitalize()} plan."
        if payment:
            message += f" Test payment of ${payment.amount} recorded."
        flash(message, "success")
    return redirect(url_for("billing.plans"))
