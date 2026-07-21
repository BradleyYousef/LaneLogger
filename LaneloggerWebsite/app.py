import os

from flask import Flask
from dotenv import load_dotenv

from auth.auth import auth_bp
from routes.routes import main_bp
from database.db import close_db


# Load variables from .env
load_dotenv()


def create_app():
    app = Flask(__name__)

    # Security configuration
    secret_key = os.environ.get("SECRET_KEY")

    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY is not set. "
            "Create a .env file and add SECRET_KEY."
        )

    app.config["SECRET_KEY"] = secret_key

    # Absolute database path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    database_path = os.path.join(
        base_dir,
        "database",
        "database.db"
    )

    app.config["DATABASE"] = database_path

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Close database connections
    app.teardown_appcontext(close_db)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )