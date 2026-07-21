import os
import sqlite3
from flask import current_app, g


def get_db():
    """
    Get the SQLite database connection for the current request.
    Flask's g object ensures we reuse one connection per request.
    """
    if "db" not in g:
        db_path = current_app.config["DATABASE"]

        # Make sure the database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row

        # Enforce foreign key relationships in SQLite
        g.db.execute("PRAGMA foreign_keys = ON")

    return g.db


def close_db(exception=None):
    """
    Close the database connection at the end of the request.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()