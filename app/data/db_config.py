"""
db_config.py — SQLite database configuration and helper functions

Purpose:
    - Centralizes all database setup and connection logic.
    - Ensures a single reusable connection path for auditing, logging, or future tables.
    - Can easily expand to support migrations or external databases later (e.g., PostgreSQL).

Location:
    app/data/db_config.py

Usage:
    from data.db_config import get_connection, init_db
    conn = get_connection()
    ...
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# -------------------------------------
# Database file location and structure
# -------------------------------------
DB_PATH = Path(__file__).resolve().parent / "app.db"


def get_connection() -> sqlite3.Connection:
    """
    Returns a new SQLite connection.
    You should always close the connection when done.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # returns dict-like rows
    return conn


def init_db() -> None:
    """
    Creates base tables if they don't exist.
    Called automatically by route modules on first use.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                model TEXT NOT NULL,
                output_format TEXT NOT NULL,
                schema TEXT,
                prompt_chars INTEGER,
                input_preview TEXT,
                response_preview TEXT
            )
            """
        )

        # Optional: generic logs table for debugging or audit expansion
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_time TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT
            )
            """
        )
        conn.commit()


def log_message(level: str, message: str) -> None:
    """
    Simple logging helper that writes a log entry into the database.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO app_logs (log_time, level, message)
                VALUES (?, ?, ?)
                """,
                (datetime.utcnow().isoformat(timespec="seconds") + "Z", level, message),
            )
            conn.commit()
    except Exception:
        # Fails silently to avoid breaking the app during logging
        pass


# Run init automatically if imported directly
if __name__ == "__main__":
    init_db()
    print(f"Database initialized at: {DB_PATH}")
