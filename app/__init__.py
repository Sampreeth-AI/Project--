"""Flask application factory for CareMatch AI."""
import os

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "development-only-secret"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///carematch.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    )
    db.init_app(app)

    from app.api import api
    app.register_blueprint(api, url_prefix="/api/v1")

    @app.get("/")
    def home():
        return render_template("index.html")

    with app.app_context():
        from app.models import DuplicateMatch, Patient  # Register tables.
        db.create_all()
    return app
