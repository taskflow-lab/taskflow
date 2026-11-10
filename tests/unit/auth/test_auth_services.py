import pytest

from app.modules.auth import services


# ---------- register_user ----------

def test_register_user_creates_user(app):
    user = services.register_user("jane@test.com", "Jane Doe", "password123")

    assert user.id is not None
    assert user.email == "jane@test.com"
    assert user.name == "Jane Doe"
    assert user.role == "member"


def test_register_user_normalizes_email(app):
    user = services.register_user("  Jane@Test.COM ", "Jane", "password123")
    assert user.email == "jane@test.com"


def test_register_user_does_not_store_plain_password(app):
    user = services.register_user("jane@test.com", "Jane", "password123")
    assert user.password_hash != "password123"
    assert user.check_password("password123")


@pytest.mark.parametrize(
    "email, name, password, message",
    [
        ("not-an-email", "Jane", "password123", "valid email"),
        ("jane@test.com", "", "password123", "Name is required"),
        ("jane@test.com", "Jane", "short", "at least 8 characters"),
        ("jane@test.com", "J" * 121, "password123", "120 characters"),
    ],
)
def test_register_user_rejects_invalid_input(app, email, name, password, message):
    with pytest.raises(ValueError, match=message):
        services.register_user(email, name, password)


def test_register_user_rejects_duplicate_email(app, user):
    with pytest.raises(ValueError, match="already exists"):
        services.register_user(user.email.upper(), "Someone Else", "password123")


def test_register_user_rejects_unknown_role(app):
    with pytest.raises(ValueError, match="Role must be one of"):
        services.register_user("jane@test.com", "Jane", "password123", role="superuser")


# ---------- authenticate ----------

def test_authenticate_with_correct_password(app, user):
    assert services.authenticate("alice@test.com", "password123") == user


def test_authenticate_is_case_insensitive_for_email(app, user):
    assert services.authenticate("ALICE@test.com", "password123") == user


@pytest.mark.parametrize(
    "email, password",
    [
        ("alice@test.com", "wrong-password"),
        ("nobody@test.com", "password123"),
        ("alice@test.com", ""),
    ],
)
def test_authenticate_fails(app, user, email, password):
    assert services.authenticate(email, password) is None


# ---------- API tokens ----------

def test_token_round_trip_returns_same_user(app, user):
    token = services.generate_api_token(user)
    assert services.get_user_by_token(token) == user


@pytest.mark.parametrize("token", ["", None, "garbage", "a.b.c"])
def test_invalid_token_returns_none(app, token):
    assert services.get_user_by_token(token) is None


def test_expired_token_returns_none(app, user):
    token = services.generate_api_token(user)
    app.config["API_TOKEN_MAX_AGE_SECONDS"] = -1
    assert services.get_user_by_token(token) is None


def test_token_signed_with_other_key_is_rejected(app, user):
    token = services.generate_api_token(user)
    app.config["SECRET_KEY"] = "a-different-secret"
    assert services.get_user_by_token(token) is None


# ---------- User model ----------

@pytest.mark.parametrize(
    "name, initials",
    [("Alice Owner", "AO"), ("Madonna", "MA"), ("Mary Jane Watson", "MW"), ("   ", "?")],
)
def test_user_initials(app, make_user, name, initials):
    user = make_user(name="Temp")
    user.name = name
    assert user.initials == initials


def test_to_dict_never_exposes_password(app, user):
    data = user.to_dict()
    assert "password" not in data
    assert "password_hash" not in data
    assert data["email"] == "alice@test.com"
