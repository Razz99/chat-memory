from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP
from app.mcp.db.queries import get_memory_by_id, save_memory, search_memories, update_memory
from app.mcp.db.setup import setup_db
from app.mcp.embedding.embedding import get_embedding

@asynccontextmanager
async def lifespan(server):
    setup_db()
    yield

mcp = FastMCP("ChatMemory", lifespan=lifespan)

@mcp.tool()
async def memorize(project_id: str, chat_title: str, chat_content: str):
    """Saves conversation or it's summary in memory so that it can be retrieved later and used as context.

    Args:
        project_id: Name of the current project.
        chat_title: The title of the current chat session.
        chat_content: The content of the chat that needs to be memorized. This can be a summary of the conversation or the entire conversation depending on the use case.
    """

    embedding = get_embedding(chat_content)

    memory_id = save_memory(
        project_name=project_id,
        chat_title=chat_title,
        content=chat_content,
        embedding=embedding,
    )

    return f"Memory saved with id={memory_id}"

@mcp.tool()
async def override_memory(memory_id: int, new_content: str) -> str:
    """Override an existing content in memory with new content.

    Args:
        memory_id: The ID of the memory to override.
        new_content: The new content to replace the existing memory content.
    """

    new_embedding = get_embedding(new_content)
    
    found = update_memory(memory_id, new_content, new_embedding)

    if not found:
        return f"No memory found with id={memory_id}"

    return f"Memory with id={memory_id} has been updated."

@mcp.tool()
async def recall_by_id(memory_id: int) -> str:
    """Recall a specific memory by its ID.

    Args:
        memory_id: The ID of the memory to recall.
    """

    memory = get_memory_by_id(memory_id)

    if memory is None:
        return f"No memory found with id={memory_id}"

    return memory["content"]

@mcp.tool()
async def recall(project_id: str, user_query: str) -> str:
    """Get context from the memory store.

    Args:
        project_id: Name of the current project.
        user_query: The user's query to fetch relevant context from memory store.
    """

    query_embedding = get_embedding(user_query)
    
    results = search_memories(project_id, query_embedding, 1)

    if not results:
        return "No relevant memories found for this project."

    return results[0]["content"]