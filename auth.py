import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, current_app,
)
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db

bp = Blueprint("auth", __name__)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


def current_user():
    if session.get("user_id"):
        db = get_db()
        return db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    return None


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if not username or not password:
            flash("Заполните все поля")
            return redirect(url_for("auth.register"))

        db = get_db()
        count = db.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        if count >= current_app.config["MAX_USERS"]:
            flash(f"Достигнут лимит пользователей ({current_app.config['MAX_USERS']})")
            return redirect(url_for("auth.register"))

        try:
            db.execute(
                "INSERT INTO users (username, password_hash, created_at, initial_balance) "
                "VALUES (?, ?, ?, ?)",
                (username, generate_password_hash(password),
                 datetime.now().isoformat(timespec="seconds"), 0),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("Такой логин уже занят")
            return redirect(url_for("auth.register"))

        flash("Аккаунт создан, войдите")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("cars.index"))
        flash("Неверный логин или пароль")
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))