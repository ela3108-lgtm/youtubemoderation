import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "moderation.db")


def get_connection():
    """Return a new database connection."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_database():
    """Initialize all tables with required schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Comments table (full schema)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            youtube_comment_id TEXT,
            author TEXT,
            text TEXT,
            toxic REAL,
            severe REAL,
            obscene REAL,
            threat REAL,
            insult REAL,
            hate REAL,
            final_decision TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            toxic_threshold REAL,
            severe_threshold REAL,
            flag_threshold REAL
        )
    """)

    # Insert default settings if missing
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO settings (id, toxic_threshold, severe_threshold, flag_threshold)
            VALUES (1, 0.6, 0.75, 0.6)
        """)

    conn.commit()
    conn.close()


def save_comment(data: dict):
    """Insert a processed comment into DB."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO comments (
            youtube_comment_id, author, text,
            toxic, severe, obscene, threat, insult, hate,
            final_decision
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("youtube_comment_id"),
        data.get("author"),
        data.get("text"),
        data.get("toxic"),
        data.get("severe"),
        data.get("obscene"),
        data.get("threat"),
        data.get("insult"),
        data.get("hate"),
        data.get("final_decision"),
    ))

    conn.commit()
    conn.close()


def fetch_recent_comments(limit=50):
    """Return recent comments."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT text, final_decision, timestamp
        FROM comments
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    return rows


def fetch_all_comments():
    """Return all comments (for dashboard)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM comments
        ORDER BY timestamp DESC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_settings():
    """Get moderation settings."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    return {
        "toxic_threshold": row[1],
        "severe_threshold": row[2],
        "flag_threshold": row[3]
    }


def update_settings(toxic, severe, flag):
    """Update moderation settings."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE settings
        SET toxic_threshold = ?, severe_threshold = ?, flag_threshold = ?
        WHERE id = 1
    """, (toxic, severe, flag))

    conn.commit()
    conn.close()


# Initialize DB when module loads
init_database()
def comment_exists(youtube_comment_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM comments WHERE youtube_comment_id = ?",
                   (youtube_comment_id,))
    exists = cursor.fetchone() is not None

    conn.close()
    return exists