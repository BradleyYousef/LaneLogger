from flask import Blueprint, render_template

main_routes = Blueprint('main', __name__)

@main_routes.route("/")
def login():
    return render_template("login.html")

@main_routes.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")