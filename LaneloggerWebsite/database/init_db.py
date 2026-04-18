import sqlite3
import os

def init_db():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "database.db")

    os.makedirs(BASE_DIR, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
    -- USERS
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password BLOB NOT NULL
    );

    -- MEETS (new)
    CREATE TABLE IF NOT EXISTS meets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        date TEXT,
        location TEXT
    );

    -- ATHLETES
    CREATE TABLE IF NOT EXISTS athletes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        team TEXT
    );

    -- EVENTS (now linked to meets)
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meet_id INTEGER,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        discipline TEXT NOT NULL,
        age_group TEXT,
        gender_group TEXT,
        date TEXT,
        location TEXT,
        lanes INTEGER DEFAULT 8,
        heats INTEGER DEFAULT 1,
        FOREIGN KEY (meet_id) REFERENCES meets(id)
    );

    -- EVENT PARTICIPANTS
    CREATE TABLE IF NOT EXISTS event_participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        athlete_id INTEGER NOT NULL,
        heat_number INTEGER NOT NULL,
        lane INTEGER,
        FOREIGN KEY (event_id) REFERENCES events(id),
        FOREIGN KEY (athlete_id) REFERENCES athletes(id)
    );

    -- RESULTS
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        athlete_id INTEGER NOT NULL,
        heat_number INTEGER NOT NULL,
        result_value REAL,
        attempt_number INTEGER DEFAULT 1,
        position INTEGER,
        FOREIGN KEY (event_id) REFERENCES events(id),
        FOREIGN KEY (athlete_id) REFERENCES athletes(id)
    );
    """)

    conn.commit()
    conn.close()

    print("Database initialized correctly.")


if __name__ == "__main__":
    init_db()
