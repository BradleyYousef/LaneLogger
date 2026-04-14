from flask import Blueprint, render_template
from auth.auth import login_user, register_user

main_routes = Blueprint('main', __name__)

@main_routes.route("/")
def home():
    return render_template("login.html")

@main_routes.route("/login", methods=["POST"])
def login():
    return login_user()

@main_routes.route("/register", methods=["POST"])
def register():
    return register_user()

@main_routes.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")