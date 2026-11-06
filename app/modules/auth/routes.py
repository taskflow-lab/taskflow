from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, StringField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from app.modules.auth import services

bp = Blueprint("auth", __name__, url_prefix="/auth")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Keep me logged in")


class RegisterForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=services.MIN_PASSWORD_LENGTH)]
    )
    confirm = PasswordField(
        "Confirm password", validators=[DataRequired(), EqualTo("password", "Passwords must match")]
    )


def safe_next_url(target):
    if not target:
        return None
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not target.startswith("/"):
        return None
    return target


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("projects.list_projects"))

    form = LoginForm()
    if form.validate_on_submit():
        user = services.authenticate(form.email.data, form.password.data)
        if user:
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(safe_next_url(request.args.get("next")) or url_for("projects.list_projects"))
        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("projects.list_projects"))

    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = services.register_user(form.email.data, form.name.data, form.password.data)
        except ValueError as error:
            form.email.errors.append(str(error))
        else:
            login_user(user)
            flash("Your account is ready. Create your first project!", "success")
            return redirect(url_for("projects.list_projects"))

    return render_template("auth/register.html", form=form)


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
