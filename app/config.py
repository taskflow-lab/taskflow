import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    APP_NAME = "TaskFlow"
    APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'taskflow.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WTF_CSRF_ENABLED = True

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    API_TOKEN_MAX_AGE_SECONDS = int(os.getenv("API_TOKEN_MAX_AGE_SECONDS", 60 * 60 * 24))

    PLAN_LIMITS = {
        "free": {"max_projects": 3, "price_monthly": 0},
        "standard": {"max_projects": 10, "price_monthly": 8},
        "premium": {"max_projects": None, "price_monthly": 15},
    }
    DEFAULT_PLAN = "free"

    ISSUE_STATUSES = ["todo", "in_progress", "in_review", "done"]
    ISSUE_TYPES = ["task", "bug", "story"]
    ISSUE_PRIORITIES = ["lowest", "low", "medium", "high", "highest"]


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret"


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def validate(cls):
        if cls.SECRET_KEY == "dev-secret-change-me":
            raise RuntimeError("SECRET_KEY must be set in production")


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    name = name or os.getenv("FLASK_ENV_NAME", "development")
    if name not in CONFIGS:
        raise ValueError(f"Unknown config '{name}'. Use one of: {', '.join(CONFIGS)}")
    return CONFIGS[name]
