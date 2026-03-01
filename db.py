import logging
from typing import Any

import psycopg
from pgvector.psycopg import register_vector_async

from config import get_db_config


async def _get_connection() -> psycopg.AsyncConnection:
    config = get_db_config()
    conn = await psycopg.AsyncConnection.connect(config.dsn)
    await register_vector_async(conn)
    return conn


async def save_memory(
    project_name: str,
    chat_title: str,
    content: str,
    embedding: list[float],
) -> int:
    """Insert a memory record into the memories table and return its id."""
    conn = await _get_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO memories (project_name, chat_title, content, embedding)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (project_name, chat_title, content, embedding),
                )
                row = await cur.fetchone()
                memory_id: int = row[0]
                logging.info(f"Saved memory with id={memory_id} for project='{project_name}'")
                return memory_id
    except Exception as exc:
        raise RuntimeError(f"Failed to save memory: {exc}") from exc


async def update_memory(memory_id: int, new_content: str, new_embedding: list[float]) -> bool:
    """Update the content and embedding of an existing memory. Returns True if found, False if not."""
    conn = await _get_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE memories
                    SET content = %s, embedding = %s
                    WHERE id = %s
                    """,
                    (new_content, new_embedding, memory_id),
                )
                updated = cur.rowcount > 0
                if updated:
                    logging.info(f"Updated memory id={memory_id}")
                else:
                    logging.warning(f"No memory found with id={memory_id} to update")
                return updated
    except Exception as exc:
        raise RuntimeError(f"Failed to update memory with id={memory_id}: {exc}") from exc

async def search_memories(
    project_name: str,
    query_embedding: list[float],
    top_k: int,
) -> list[dict[str, Any]]:
    """Find the top_k most similar memories for a project using cosine similarity."""
    conn = await _get_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT content,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM memories
                    WHERE project_name = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_embedding, project_name, query_embedding, top_k),
                )
                rows = await cur.fetchall()
                return [
                    {
                        "content": row[0],
                    }
                    for row in rows
                ]
    except Exception as exc:
        raise RuntimeError(f"Failed to search memories for project='{project_name}': {exc}") from exc


async def get_memory_by_id(memory_id: int) -> dict[str, Any] | None:
    """Fetch a memory record by its id."""
    conn = await _get_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT content FROM memories
                    WHERE id = %s
                    """,
                    (memory_id,),
                )
                row = await cur.fetchone()
                if row is None:
                    return None
                return {
                    "content": row[0],
                }
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch memory with id={memory_id}: {exc}") from exc
