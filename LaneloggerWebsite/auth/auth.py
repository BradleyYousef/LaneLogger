from flask import request, redirect, session
from database.db import get_db
from utils.security import hash_password, check_password

def register_user():
    username = request.form['username']
    password = hash_password(request.form['password'])

    db = get_db()
    db.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, password)
    )
    db.commit()

    return redirect("/")

def login_user():
    username = request.form['username']
    password = request.form['password']

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()

    if user and check_password(password, user['password']):
        session['user_id'] = user['id']
        return redirect("/dashboard")

    return "Login failed"