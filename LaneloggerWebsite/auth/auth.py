from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.db import get_db
from utils.security import hash_password, check_password

auth_bp = Blueprint("auth", __name__)

# login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password(password, user["password"]):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html")

# register
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:
            flash("Passwords do not match", "danger")
            return redirect(url_for("auth.register"))

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hash_password(password))
            )
            db.commit()
            flash("Account created", "success")
            return redirect(url_for("auth.login"))
        except:
            flash("Username already taken", "danger")

    return render_template("register.html")

# logout
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))
