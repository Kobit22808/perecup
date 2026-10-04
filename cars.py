from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash,
)

from db import get_db
from auth import login_required

bp = Blueprint("cars", __name__)


@bp.route("/")
@login_required
def index():
    db = get_db()

    user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    initial_balance = (user["initial_balance"] or 0) if user else 0

    cars = db.execute(
        "SELECT * FROM cars WHERE user_id=? ORDER BY id DESC",
        (session["user_id"],),
    ).fetchall()

    active_cars = []
    sold_cars = []
    total_invested = 0.0        # все вложения — нужны для баланса
    active_invested = 0.0       # вложения только в машины в работе — для отображения
    total_sold = 0.0
    total_profit = 0.0

    for c in cars:
        records = db.execute(
            "SELECT * FROM car_items WHERE car_id=? AND user_id=? ORDER BY id DESC",
            (c["id"], session["user_id"]),
        ).fetchall()
        records_total = sum((r["amount"] or 0) for r in records)
        invested = (c["buy_price"] or 0) + (c["expenses"] or 0) + records_total
        profit = (c["sell_price"] - invested) if c["sell_price"] else 0
        total_invested += invested
        if c["sell_price"]:
            total_sold += c["sell_price"]
            total_profit += profit
        else:
            # машина ещё в работе — её вложения «заморожены» в обороте
            active_invested += invested

        car_dict = {
            **dict(c),
            "records": [dict(r) for r in records],
            "records_total": records_total,
            "invested": invested,
            "profit": profit,
        }

        if c["status"] == "продана":
            sold_cars.append(car_dict)
        else:
            active_cars.append(car_dict)

    current_balance = initial_balance - total_invested + total_sold

    return render_template(
        "index.html",
        active_cars=active_cars,
        sold_cars=sold_cars,
        total_invested=total_invested,
        active_invested=active_invested,
        total_sold=total_sold,
        total_profit=total_profit,
        initial_balance=initial_balance,
        current_balance=current_balance,
        username=session["username"],
    )


@bp.route("/set_balance", methods=["POST"])
@login_required
def set_balance():
    db = get_db()
    try:
        value = float(request.form.get("initial_balance") or 0)
    except ValueError:
        flash("Введи число")
        return redirect(url_for("cars.index"))
    db.execute("UPDATE users SET initial_balance=? WHERE id=?",
               (value, session["user_id"]))
    db.commit()
    flash("Начальный капитал обновлён")
    return redirect(url_for("cars.index"))


@bp.route("/add", methods=["POST"])
@login_required
def add():
    db = get_db()
    db.execute(
        """INSERT INTO cars (user_id, name, buy_price, expenses, sell_price, status, notes, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session["user_id"],
            request.form["name"].strip(),
            float(request.form.get("buy_price") or 0),
            float(request.form.get("expenses") or 0),
            float(request.form.get("sell_price") or 0),
            request.form.get("status") or "в работе",
            request.form.get("notes", ""),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    db.commit()
    return redirect(url_for("cars.index"))


@bp.route("/edit/<int:car_id>", methods=["POST"])
@login_required
def edit(car_id):
    db = get_db()
    car = db.execute("SELECT * FROM cars WHERE id=? AND user_id=?",
                     (car_id, session["user_id"])).fetchone()
    if not car:
        flash("Машина не найдена")
        return redirect(url_for("cars.index"))
    if car["status"] == "продана":
        flash("Проданную машину нельзя редактировать. Сначала верни её в работу.")
        return redirect(url_for("cars.index"))

    db.execute(
        """UPDATE cars SET name=?, buy_price=?, expenses=?, sell_price=?, status=?, notes=?
           WHERE id=? AND user_id=?""",
        (
            request.form["name"].strip(),
            float(request.form.get("buy_price") or 0),
            float(request.form.get("expenses") or 0),
            float(request.form.get("sell_price") or 0),
            request.form.get("status") or "в работе",
            request.form.get("notes", ""),
            car_id,
            session["user_id"],
        ),
    )
    db.commit()
    return redirect(url_for("cars.index"))


@bp.route("/unmark_sold/<int:car_id>", methods=["POST"])
@login_required
def unmark_sold(car_id):
    """Вернуть проданную машину в работу (на случай ошибки)."""
    db = get_db()
    db.execute(
        "UPDATE cars SET status='в работе' WHERE id=? AND user_id=? AND status='продана'",
        (car_id, session["user_id"]),
    )
    db.commit()
    flash("Машина возвращена в работу")
    return redirect(url_for("cars.index"))


@bp.route("/delete/<int:car_id>", methods=["POST"])
@login_required
def delete(car_id):
    db = get_db()
    db.execute("DELETE FROM car_items WHERE car_id=? AND user_id=?",
               (car_id, session["user_id"]))
    db.execute("DELETE FROM cars WHERE id=? AND user_id=?",
               (car_id, session["user_id"]))
    db.commit()
    return redirect(url_for("cars.index"))


@bp.route("/add_item", methods=["POST"])
@login_required
def add_item():
    db = get_db()
    car_id = request.form["car_id"]
    car = db.execute("SELECT * FROM cars WHERE id=? AND user_id=?",
                     (car_id, session["user_id"])).fetchone()
    if not car:
        flash("Машина не найдена")
        return redirect(url_for("cars.index"))
    if car["status"] == "продана":
        flash("Нельзя добавлять детали к проданной машине")
        return redirect(url_for("cars.index"))

    description = request.form["description"].strip()
    if not description:
        flash("Укажи, что куплено/сделано")
        return redirect(url_for("cars.index"))

    db.execute(
        """INSERT INTO car_items (car_id, user_id, kind, description, amount, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            car_id,
            session["user_id"],
            request.form.get("kind") or "деталь",
            description,
            float(request.form.get("amount") or 0),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    db.commit()
    return redirect(url_for("cars.index"))


@bp.route("/delete_item/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    db = get_db()
    # проверяем, что запись принадлежит машине пользователя и машина не продана
    item = db.execute("""
        SELECT ci.*, c.status AS car_status
        FROM car_items ci
        JOIN cars c ON c.id = ci.car_id
        WHERE ci.id=? AND ci.user_id=?
    """, (item_id, session["user_id"])).fetchone()
    if not item:
        flash("Запись не найдена")
        return redirect(url_for("cars.index"))
    if item["car_status"] == "продана":
        flash("Нельзя менять записи проданной машины")
        return redirect(url_for("cars.index"))

    db.execute("DELETE FROM car_items WHERE id=? AND user_id=?",
               (item_id, session["user_id"]))
    db.commit()
    return redirect(url_for("cars.index"))