import sqlite3
import os
from flask import g

def get_db():
    if "db" not in g:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(BASE_DIR, "database.db")

        os.makedirs(BASE_DIR, exist_ok=True)

        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()