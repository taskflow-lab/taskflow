from flask import current_app

from app.extensions import db
from app.modules.billing.models import Payment, Subscription


class PlanLimitError(PermissionError):
    status_code = 402


def _plans_config():
    return current_app.config["PLAN_LIMITS"]


def list_plans():
    return [
        {
            "code": code,
            "name": code.capitalize(),
            "price_monthly": limits["price_monthly"],
            "max_projects": limits["max_projects"],
        }
        for code, limits in _plans_config().items()
    ]


def get_plan_limit(plan_code):
    if plan_code not in _plans_config():
        raise ValueError(f"Unknown plan '{plan_code}'")
    return _plans_config()[plan_code]["max_projects"]


def get_subscription(user):
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    if subscription is None:
        subscription = Subscription(user_id=user.id, plan=current_app.config["DEFAULT_PLAN"])
        db.session.add(subscription)
        db.session.commit()
    return subscription


def check_project_limit(user, current_project_count):
    plan = get_subscription(user).plan
    limit = get_plan_limit(plan)
    if limit is not None and current_project_count >= limit:
        raise PlanLimitError(
            f"Your {plan.capitalize()} plan allows {limit} active projects. Upgrade to create more."
        )


def _count_owned_projects(user):
    from app.modules.projects.services import count_active_owned_projects

    return count_active_owned_projects(user)


def get_usage(user):
    subscription = get_subscription(user)
    limit = get_plan_limit(subscription.plan)
    used = _count_owned_projects(user)
    return {
        "plan": subscription.plan,
        "projects_used": used,
        "projects_limit": limit,
        "projects_remaining": None if limit is None else max(limit - used, 0),
    }


def change_plan(user, plan_code):
    plan_code = (plan_code or "").strip().lower()
    new_limit = get_plan_limit(plan_code)

    subscription = get_subscription(user)
    if subscription.plan == plan_code:
        raise ValueError(f"You are already on the {plan_code.capitalize()} plan")

    used = _count_owned_projects(user)
    if new_limit is not None and used > new_limit:
        raise PlanLimitError(
            f"You have {used} active projects but the {plan_code.capitalize()} plan allows {new_limit}. "
            "Archive some projects first."
        )

    payment = None
    price = _plans_config()[plan_code]["price_monthly"]
    if price > 0:
        payment = Payment(user_id=user.id, plan=plan_code, amount=price)
        db.session.add(payment)

    subscription.plan = plan_code
    subscription.status = "active"
    db.session.commit()
    return subscription, payment
