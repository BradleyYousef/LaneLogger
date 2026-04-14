import os
from flask import Flask, request, render_template
from routes.routes import main_routes

app = Flask(__name__)
app.secret_key = "secret123"

app.register_blueprint(main_routes)

if __name__ == "__main__":
    app.run(debug=True)