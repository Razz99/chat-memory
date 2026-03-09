import sqlite3
import sqlite_vec

from sqlite_vec import serialize_float32
from app.mcp.db.setup import get_db_path

def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())

    conn.enable_load_extension(True)

    sqlite_vec.load(conn)

    conn.enable_load_extension(False)

    conn.row_factory = sqlite3.Row

    return conn

def save_memory(
    project_name: str,
    chat_title: str,
    content: str,
    embedding: list[float],
) -> int:
    conn = _get_connection()

    try:
        with conn:
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO memories (project_name, chat_title, content) VALUES (?, ?, ?)",
                (project_name, chat_title, content),
            )

            memory_id: int = cur.lastrowid
            
            cur.execute(
                "INSERT INTO memories_vec (memory_id, embedding) VALUES (?, ?)",
                (memory_id, serialize_float32(embedding)),
            )

        return memory_id
    finally:
        conn.close()

def get_memory_by_id(memory_id: int) -> dict[str, str] | None:
    conn = _get_connection()

    try:
        cur = conn.execute("SELECT content FROM memories WHERE id = ?", (memory_id,))

        row = cur.fetchone()

        return {"content": row["content"]} if row else None
    finally:
        conn.close()

def update_memory(
    memory_id: int,
    new_content: str,
    new_embedding: list[float],
) -> bool:
    conn = _get_connection()

    try:
        with conn:
            cur = conn.cursor()

            cur.execute(
                "UPDATE memories SET content = ? WHERE id = ?",
                (new_content, memory_id),
            )

            if cur.rowcount == 0:
                return False
            
            cur.execute(
                "UPDATE memories_vec SET embedding = ? WHERE memory_id = ?",
                (serialize_float32(new_embedding), memory_id),
            )

        return True
    finally:
        conn.close()

def search_memories(
    project_name: str,
    query_embedding: list[float],
    top_k: int,
) -> list[dict[str, str]]:
    conn = _get_connection()

    try:
        cur = conn.execute(
            """
            SELECT m.content, vec_distance_cosine(v.embedding, ?) AS distance
            FROM memories_vec v
            JOIN memories m ON m.id = v.memory_id
            WHERE m.project_name = ?
            ORDER BY distance
            LIMIT ?
            """,
            (serialize_float32(query_embedding), project_name, top_k),
        )

        return [{"content": row["content"]} for row in cur.fetchall()]
    finally:
        conn.close()
