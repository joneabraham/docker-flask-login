from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import text

from . import db
from .models import User

auth_bp = Blueprint("auth", __name__)
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    return render_template("dashboard.html", user=current_user)


@main_bp.route("/health")
def health():
    """Liveness + DB connectivity check used by Docker Compose healthcheck."""
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify(status="ok", database="up"), 200
    except Exception as exc:  # pragma: no cover - only hit when DB is down
        return jsonify(status="degraded", database="down", error=str(exc)), 503


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3 or len(password) < 8:
            flash("Username needs 3+ characters and password 8+ characters.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("That username is already taken.", "danger")
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=bool(request.form.get("remember")))
            return redirect(url_for("main.index"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
