import sqlite3
import os
import sqlite_vec

from pathlib import Path

def get_db_path() -> Path:
    custom = os.getenv("CHAT_MEMORY_DB_PATH")

    return Path(custom) if custom else Path.home() / ".chat-memory" / "memories.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())

    conn.enable_load_extension(True)

    sqlite_vec.load(conn)

    conn.enable_load_extension(False)

    conn.row_factory = sqlite3.Row

    return conn

def setup_db() -> None:
    db_path = get_db_path()

    db_path.parent.mkdir(parents=True, exist_ok=True)

    setup_query = """
        -- Main memories table
        CREATE TABLE IF NOT EXISTS memories (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            chat_title   TEXT NOT NULL,
            content      TEXT NOT NULL,
            created_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Vector virtual table using sqlite-vec
        -- Stores 768-dim embeddings
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0(
            memory_id INTEGER PRIMARY KEY,
            embedding float[768]
        );
    """

    conn = get_connection()

    try:
        conn.executescript(setup_query)
        
        conn.commit()
    finally:
        conn.close()
