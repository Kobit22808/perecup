from flask import Flask

from config import Config
import db
from auth import bp as auth_bp
from cars import bp as cars_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.init_db()

    app.register_blueprint(auth_bp)
    app.register_blueprint(cars_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)