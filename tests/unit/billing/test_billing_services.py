
import pytest

from app.modules.billing import services
from app.modules.billing.models import Payment


# ---------- plans ----------

def test_list_plans_returns_all_three(app):
    codes = [plan["code"] for plan in services.list_plans()]
    assert codes == ["free", "standard", "premium"]


@pytest.mark.parametrize("plan, limit", [("free", 3), ("standard", 10), ("premium", None)])
def test_get_plan_limit(app, plan, limit):
    assert services.get_plan_limit(plan) == limit


def test_get_plan_limit_unknown_plan(app):
    with pytest.raises(ValueError, match="Unknown plan"):
        services.get_plan_limit("gold")


# ---------- subscription ----------

def test_new_user_starts_on_free_plan(app, user):
    assert services.get_subscription(user).plan == "free"


def test_get_subscription_does_not_create_duplicates(app, user):
    first = services.get_subscription(user)
    second = services.get_subscription(user)
    assert first.id == second.id


# ---------- check_project_limit ----------

@pytest.mark.parametrize("count", [0, 1, 2])
def test_free_plan_allows_up_to_three_projects(app, user, count):
    services.check_project_limit(user, count)  # no error raised


def test_free_plan_blocks_fourth_project(app, user):
    with pytest.raises(services.PlanLimitError, match="allows 3 active projects"):
        services.check_project_limit(user, 3)


def test_premium_plan_has_no_limit(app, user, set_plan):
    set_plan(user, "premium")
    services.check_project_limit(user, 500)  # no error raised


def test_plan_limit_error_maps_to_http_402(app):
    assert services.PlanLimitError.status_code == 402


def test_limit_comes_from_config(app, user):
    app.config["PLAN_LIMITS"]["free"]["max_projects"] = 1
    with pytest.raises(services.PlanLimitError, match="allows 1 active projects"):
        services.check_project_limit(user, 1)


# ---------- change_plan ----------

def test_upgrade_records_mock_payment(app, user):
    subscription, payment = services.change_plan(user, "standard")

    assert subscription.plan == "standard"
    assert payment.amount == 8
    assert payment.is_mock is True
    assert Payment.query.count() == 1


def test_downgrade_to_free_has_no_payment(app, user, set_plan):
    set_plan(user, "standard")
    subscription, payment = services.change_plan(user, "free")

    assert subscription.plan == "free"
    assert payment is None


def test_change_plan_accepts_messy_input(app, user):
    subscription, _ = services.change_plan(user, "  PREMIUM ")
    assert subscription.plan == "premium"


def test_change_to_same_plan_is_rejected(app, user):
    with pytest.raises(ValueError, match="already on the Free plan"):
        services.change_plan(user, "free")


def test_change_to_unknown_plan_is_rejected(app, user):
    with pytest.raises(ValueError, match="Unknown plan"):
        services.change_plan(user, "gold")


# ---------- usage ----------

def test_usage_for_new_user(app, user):
    assert services.get_usage(user) == {
        "plan": "free",
        "projects_used": 0,
        "projects_limit": 3,
        "projects_remaining": 3,
    }


def test_usage_on_premium_is_unlimited(app, user, set_plan):
    set_plan(user, "premium")
    usage = services.get_usage(user)
    assert usage["projects_limit"] is None
    assert usage["projects_remaining"] is None
