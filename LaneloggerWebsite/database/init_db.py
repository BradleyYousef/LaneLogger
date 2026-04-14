from db import get_db

db = get_db()

db.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

db.commit()
print("Database created successfully!")