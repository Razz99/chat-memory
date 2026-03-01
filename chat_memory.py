from typing import Any
import asyncio
import os
import requests
from mcp.server.fastmcp import FastMCP

import logging

from db import save_memory, get_memory_by_id, update_memory, search_memories

REQUEST_TIMEOUT_SECONDS = 60

def get_embedding(text_content: str) -> Any:
    proxy_url = os.getenv("LLM_PROXY_BASE_URL")
    proxy_api_key = os.getenv("LLM_PROXY_API_KEY")

    if not proxy_url or not proxy_api_key:
        raise ValueError("Set LLM_PROXY_BASE_URL and LLM_PROXY_API_KEY environment variables")

    endpoint = f"{proxy_url}/embeddings"

    headers = {
        "Authorization": f"Bearer {proxy_api_key}",
    }

    payload = {
        "model": "text-embedding-005",
        "input": text_content
    }

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Embedding request failed: {exc}") from exc

    data = response.json()
    return data["data"][0]["embedding"]

# Initialize FastMCP server
mcp = FastMCP("ChatMemory")

@mcp.tool()
async def memorize(project_id: str, chat_title: str, chat_content: str):
    """Saves conversation summary in memory so that it can be retrieved later and used as context.

    Args:
        project_id: Name of the current project.
        chat_title: The title of the copilot chat session.
        chat_content: The content of the chat that needs to be memorized. This can be a summary of the conversation or the entire conversation depending on the use case.
    """

    embedding = await asyncio.to_thread(get_embedding, chat_content)

    memory_id = await save_memory(
        project_name=project_id,
        chat_title=chat_title,
        content=chat_content,
        embedding=embedding,
    )

    return f"Memory saved with id={memory_id}"

@mcp.tool()
async def recall(project_id: str, user_query: str) -> str:
    """Get context from the memory store.

    Args:
        project_id: The ID of the project
        user_query: The user's query to fetch relevant context
    """
    logging.info(f"Fetching context for project {project_id} with query '{user_query}'")
    query_embedding = await asyncio.to_thread(get_embedding, user_query)
    results = await search_memories(project_name=project_id, query_embedding=query_embedding, top_k=1)

    if not results:
        return "No relevant memories found for this project."

    return results[0]["content"]

@mcp.tool()
async def recall_by_id(memory_id: int) -> str:
    """Recall a specific memory by its ID.

    Args:
        memory_id: The ID of the memory to recall
    """

    memory = await get_memory_by_id(memory_id)

    if memory is None:
        return f"No memory found with id={memory_id}"

    return memory["content"]

@mcp.tool()
async def override_memory(memory_id: int, new_content: str) -> str:
    """Override an existing memory with new content.

    Args:
        memory_id: The ID of the memory to override
        new_content: The new content to replace the existing memory content
    """
    new_embedding = await asyncio.to_thread(get_embedding, new_content)
    found = await update_memory(memory_id, new_content, new_embedding)

    if not found:
        return f"No memory found with id={memory_id}"

    return f"Memory with id={memory_id} has been updated."