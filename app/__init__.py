from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from app.config import get_config
from app.extensions import csrf, db, login_manager

MODULES = ["auth", "projects", "issues", "board", "search", "notifications", "billing", "health"]


def create_app(config_name=None):
    app = Flask(__name__)
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    if hasattr(config_class, "validate"):
        config_class.validate()

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    register_extensions(app)
    register_models()
    register_blueprints(app)
    register_error_handlers(app)
    register_context(app)
    register_commands(app)

    with app.app_context():
        db.create_all()

    return app


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)


def register_models():
    import importlib

    for module in MODULES:
        importlib.import_module(f"app.modules.{module}.models")


def register_blueprints(app):
    import importlib

    from app.api import api_v1_bp

    for module in MODULES:
        routes = importlib.import_module(f"app.modules.{module}.routes")
        app.register_blueprint(routes.bp)

    csrf.exempt(api_v1_bp)
    app.register_blueprint(api_v1_bp)

    @app.get("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("projects.list_projects"))
        return redirect(url_for("auth.login"))


def wants_json():
    return request.path.startswith("/api/")


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        if wants_json():
            return jsonify({"error": {"status": 404, "message": "Not found"}}), 404
        return render_template("layouts/error.html", code=404, message="Page not found"), 404

    @app.errorhandler(403)
    def forbidden(error):
        if wants_json():
            return jsonify({"error": {"status": 403, "message": "Forbidden"}}), 403
        return render_template("layouts/error.html", code=403, message="You don't have access to this page"), 403

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        if wants_json():
            return jsonify({"error": {"status": 500, "message": "Internal server error"}}), 500
        return render_template("layouts/error.html", code=500, message="Something went wrong"), 500


def register_context(app):
    @app.context_processor
    def inject_globals():
        unread = 0
        if current_user.is_authenticated:
            from app.modules.notifications.services import unread_count

            unread = unread_count(current_user)
        return {
            "app_name": app.config["APP_NAME"],
            "app_version": app.config["APP_VERSION"],
            "unread_notifications": unread,
        }


def register_commands(app):
    @app.cli.command("init-db")
    def init_db():
        db.drop_all()
        db.create_all()
        print("Database reset.")
