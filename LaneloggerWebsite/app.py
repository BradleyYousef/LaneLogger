from flask import Flask
from auth.auth import auth_bp
from routes.routes import main_bp
from database.db import close_db

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-this-secret"
    app.config["DATABASE"] = "database/database.db"

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    app.teardown_appcontext(close_db)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
