import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-to-random-string")
    DATABASE = os.path.join(BASE_DIR, "auto.db")
    MAX_USERS = 10