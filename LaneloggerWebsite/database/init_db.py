import os
import sqlite3


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")


def init_db():
    os.makedirs(BASE_DIR, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)

    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON")

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS athletes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            athlete_number INTEGER NOT NULL,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            team TEXT,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            UNIQUE(user_id, athlete_number)
        );

        CREATE TABLE IF NOT EXISTS meets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            date TEXT,
            location TEXT,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meet_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            discipline TEXT NOT NULL,
            age_group TEXT,
            gender_group TEXT,
            event_date TEXT,
            location TEXT,
            lanes INTEGER NOT NULL DEFAULT 8,
            heats INTEGER NOT NULL DEFAULT 1,

            FOREIGN KEY (meet_id)
                REFERENCES meets(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            athlete_id INTEGER NOT NULL,
            heat_number INTEGER NOT NULL,
            lane INTEGER NOT NULL,

            FOREIGN KEY (event_id)
                REFERENCES events(id)
                ON DELETE CASCADE,

            FOREIGN KEY (athlete_id)
                REFERENCES athletes(id)
                ON DELETE CASCADE,

            UNIQUE(event_id, heat_number, lane),
            UNIQUE(event_id, heat_number, athlete_id)
        );

        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            athlete_id INTEGER NOT NULL,
            heat_number INTEGER NOT NULL,
            lane INTEGER NOT NULL,
            result_value REAL,
            result_status TEXT DEFAULT 'valid',
            attempt_number INTEGER DEFAULT 1,
            position INTEGER,

            FOREIGN KEY (event_id)
                REFERENCES events(id)
                ON DELETE CASCADE,

            FOREIGN KEY (athlete_id)
                REFERENCES athletes(id)
                ON DELETE CASCADE
        );
        """
    )

    conn.commit()
    conn.close()

    print("Database initialized successfully.")
    print(f"Database location: {DATABASE_PATH}")


if __name__ == "__main__":
    init_db()