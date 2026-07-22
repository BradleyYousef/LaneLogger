import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")


def init_db():

    # Make sure the database directory exists
    os.makedirs(BASE_DIR, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)

    conn.execute("PRAGMA foreign_keys = ON")

    cursor = conn.cursor()

    cursor.executescript(
        """
        --------------------------------------------------
        -- USERS
        --------------------------------------------------

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );


        --------------------------------------------------
        -- ATHLETES
        --------------------------------------------------

        CREATE TABLE IF NOT EXISTS athletes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            athlete_number INTEGER NOT NULL,

            name TEXT NOT NULL,

            age INTEGER,

            gender TEXT,

            team TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
            
            
            UNIQUE (user_id, athlete_number)
        );


        --------------------------------------------------
        -- MEETS
        --------------------------------------------------

        CREATE TABLE IF NOT EXISTS meets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            date TEXT,

            location TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );


        --------------------------------------------------
        -- EVENTS
        --------------------------------------------------

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            meet_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            type TEXT NOT NULL,

            discipline TEXT NOT NULL,

            age_group TEXT,

            gender_group TEXT,

            event_date TEXT,

            location TEXT,

            lanes INTEGER DEFAULT 8,

            heats INTEGER DEFAULT 1,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (meet_id)
                REFERENCES meets(id)
                ON DELETE CASCADE
        );


        --------------------------------------------------
        -- EVENT PARTICIPANTS
        --------------------------------------------------

        CREATE TABLE IF NOT EXISTS event_participants (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            event_id INTEGER NOT NULL,

            athlete_id INTEGER NOT NULL,

            heat_number INTEGER NOT NULL,

            lane INTEGER NOT NULL,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (event_id)
                REFERENCES events(id)
                ON DELETE CASCADE,

            FOREIGN KEY (athlete_id)
                REFERENCES athletes(id)
                ON DELETE CASCADE,

            UNIQUE (
                user_id,
                event_id,
                heat_number,
                lane
            )

        );


        --------------------------------------------------
        -- RESULTS
        --------------------------------------------------

        CREATE TABLE IF NOT EXISTS results (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            event_id INTEGER NOT NULL,

            athlete_id INTEGER NOT NULL,

            heat_number INTEGER NOT NULL,

            lane INTEGER,

            result_value REAL,

            attempt_number INTEGER DEFAULT 1,

            position INTEGER,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (event_id)
                REFERENCES events(id)
                ON DELETE CASCADE,

            FOREIGN KEY (athlete_id)
                REFERENCES athletes(id)
                ON DELETE CASCADE

        );


        --------------------------------------------------
        -- INDEXES
        --------------------------------------------------

        CREATE INDEX IF NOT EXISTS idx_athletes_user_id
        ON athletes(user_id);


        CREATE INDEX IF NOT EXISTS idx_meets_user_id
        ON meets(user_id);


        CREATE INDEX IF NOT EXISTS idx_events_user_id
        ON events(user_id);


        CREATE INDEX IF NOT EXISTS idx_events_meet_id
        ON events(meet_id);


        CREATE INDEX IF NOT EXISTS idx_participants_user_id
        ON event_participants(user_id);


        CREATE INDEX IF NOT EXISTS idx_participants_event_id
        ON event_participants(event_id);


        CREATE INDEX IF NOT EXISTS idx_results_user_id
        ON results(user_id);


        CREATE INDEX IF NOT EXISTS idx_results_event_id
        ON results(event_id);

        """
    )

    conn.commit()
    conn.close()

    print("Database initialized successfully.")
    print(f"Database location: {DATABASE_PATH}")


if __name__ == "__main__":
    init_db()