# Chat Memory — Agent Guide

## Project Overview

`chat-memory` is an MCP (Model Context Protocol) server that provides persistent memory capabilities for AI chat sessions. It stores conversation or its summaries as vector embeddings in a local SQLite database (via `sqlite-vec`) and enables semantic similarity search to retrieve relevant past context.

---

## Architecture

```
main.py                          # Entrypoint — starts the MCP server over stdio
app/
  mcp/
    server.py                    # MCP tool definitions (memorize, recall, override_memory, recall_by_id)
    db/
      setup.py                   # DB path resolution, connection factory, schema setup
      queries.py                 # CRUD + vector similarity search queries
    embedding/
      embedding.py               # HTTP call to external LLM proxy for text embeddings
```

### Data Flow

1. **Memorize**: `chat_content` → `get_embedding()` → `save_memory()` → stored in `memories` + `memories_vec` tables
2. **Recall**: `user_query` → `get_embedding()` → `search_memories()` → cosine similarity search → top result returned
3. **Override**: `new_content` → `get_embedding()` → `update_memory()` → updates both tables
4. **Recall by ID**: direct row lookup by `memory_id`

---

## Database

- **Engine**: SQLite with the [`sqlite-vec`](https://github.com/asg017/sqlite-vec) extension
- **Default path**: `~/.chat-memory/memories.db`
- **Override path**: Set the `CHAT_MEMORY_DB_PATH` environment variable
- **Schema**:
  - `memories` — stores `project_name`, `chat_title`, `content`, `created_at`
  - `memories_vec` — virtual table storing `float[768]` embeddings, linked by `memory_id`
- **Embedding dimensions**: 768 (matches `text-embedding-005`)

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `LLM_PROXY_BASE_URL` | ✅ Yes | Base URL of the LLM proxy (e.g. `https://proxy.example.com`) |
| `LLM_PROXY_API_KEY` | ✅ Yes | API key for authenticating with the LLM proxy |
| `CHAT_MEMORY_DB_PATH` | ❌ Optional | Custom path for the SQLite database file |

---

## MCP Tools

| Tool | Description |
|---|---|
| `memorize(project_id, chat_title, chat_content)` | Embeds and saves a conversation or summary |
| `recall(project_id, user_query)` | Retrieves the most semantically similar memory for a project |
| `recall_by_id(memory_id)` | Retrieves a specific memory by its integer ID |
| `override_memory(memory_id, new_content)` | Replaces an existing memory's content and re-embeds it |

---

## Setup & Running

### Install dependencies

```sh
uv sync
```

### Run the MCP server

```sh
uv run main.py
```

The server communicates over **stdio** using the MCP protocol.

### Test if sqlite-vec setup is working in your system

```sh
uv run test_sqlite_vec_extension.py
```

---

## Building a Standalone Binary

Uses PyInstaller via the [`chat-memory.spec`](chat-memory.spec) file:

```sh
uv run pyinstaller chat-memory.spec
```

Output binary will be in the `dist/` directory.

---

## Key Implementation Notes

- Each MCP tool invocation opens and closes its own SQLite connection — there is no shared connection pool.
- The `lifespan` context manager in [`app/mcp/server.py`](app/mcp/server.py) calls `setup_db()` once at server startup to ensure the schema exists.
- Embeddings use `serialize_float32` from `sqlite_vec` before being stored or used in similarity queries.
- The `search_memories` query uses `vec_distance_cosine` and filters by `project_name` before ranking, ensuring memory isolation between projects.