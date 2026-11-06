import time

from flask import current_app
from sqlalchemy import text

from app.extensions import db


def get_app_info():
    return {
        "service": current_app.config["APP_NAME"].lower(),
        "version": current_app.config["APP_VERSION"],
    }


def check_database():
    start = time.perf_counter()
    try:
        db.session.execute(text("SELECT 1"))
    except Exception as error:  # noqa: BLE001 - any DB failure means "not ready"
        db.session.rollback()
        return {"ok": False, "error": error.__class__.__name__}
    return {"ok": True, "latency_ms": round((time.perf_counter() - start) * 1000, 2)}


def run_readiness_checks():
    return {"database": check_database()}
