import sqlite3

def init_db():
    conn = sqlite3.connect("database/database.db")
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL
        );

        CREATE TABLE IF NOT EXISTS athletes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            team TEXT
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            discipline TEXT NOT NULL,
            age_group TEXT,
            gender_group TEXT,
            date TEXT,
            location TEXT,
            lanes INTEGER,
            heats INTEGER
        );

        CREATE TABLE IF NOT EXISTS event_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            athlete_id INTEGER NOT NULL,
            heat_number INTEGER NOT NULL,
            lane INTEGER,
            FOREIGN KEY (event_id) REFERENCES events(id),
            FOREIGN KEY (athlete_id) REFERENCES athletes(id)
        );

        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            athlete_id INTEGER NOT NULL,
            heat_number INTEGER NOT NULL,
            result_value REAL,
            attempt_number INTEGER,
            position INTEGER,
            FOREIGN KEY (event_id) REFERENCES events(id),
            FOREIGN KEY (athlete_id) REFERENCES athletes(id)
        );
        """
    )

    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()