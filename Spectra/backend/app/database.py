import sqlite3
from contextlib import contextmanager
from app.core.config import settings

@contextmanager
def get_connection():
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    finally:
        connection.close()

def initialize_database():
    with get_connection() as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS profiles (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS profile_ratings (
            profile_id INTEGER NOT NULL,
            movie_id INTEGER NOT NULL,
            rating REAL NOT NULL CHECK(rating >= 0.5 AND rating <= 5.0),
            PRIMARY KEY (profile_id, movie_id),
            FOREIGN KEY (profile_id) REFERENCES profiles(profile_id) ON DELETE CASCADE
        );
        """)

def create_profile(name: str, ratings: list[dict]) -> int:
    with get_connection() as connection:
        cursor = connection.execute("INSERT INTO profiles(name) VALUES (?)", (name,))
        profile_id = int(cursor.lastrowid)
        connection.executemany(
            "INSERT INTO profile_ratings(profile_id, movie_id, rating) VALUES (?, ?, ?)",
            [(profile_id, item["movie_id"], item["rating"]) for item in ratings],
        )
        return profile_id

def get_profile(profile_id: int):
    with get_connection() as connection:
        profile = connection.execute("SELECT profile_id, name FROM profiles WHERE profile_id=?", (profile_id,)).fetchone()
        if profile is None:
            return None
        ratings = connection.execute(
            "SELECT movie_id, rating FROM profile_ratings WHERE profile_id=? ORDER BY movie_id", (profile_id,)
        ).fetchall()
        return {"profile_id": profile["profile_id"], "name": profile["name"], "ratings": [dict(row) for row in ratings]}
