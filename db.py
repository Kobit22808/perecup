import sqlite3
import os
from flask import current_app, g


def get_db():
    """Возвращает соединение с БД в контексте текущего запроса."""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Создаёт таблицы, если их нет. Также делает миграцию для старых баз."""
    db = sqlite3.connect(current_app.config["DATABASE"])
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        db.executescript(f.read())

    # Миграция старой базы: добавить initial_balance, если её ещё нет
    cols = [r[1] for r in db.execute("PRAGMA table_info(users)").fetchall()]
    if "initial_balance" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN initial_balance REAL NOT NULL DEFAULT 0")

    db.commit()
    db.close()


def init_app(app):
    """Регистрирует хук закрытия БД."""
    app.teardown_appcontext(close_db)