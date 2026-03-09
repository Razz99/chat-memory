# chat-memory

A local MCP (Model Context Protocol) server that gives AI assistants persistent memory across chat sessions. It stores conversation summaries as vector embeddings in a local SQLite database and retrieves semantically relevant context on demand.

---

## How It Works

When you ask your AI assistant to "memorize" a conversation, it saves an embedding of that content locally on your machine. Later, when you ask it to "recall" something, it searches your saved memories using semantic similarity and returns the most relevant one as context.

All data stays on your machine — nothing is sent to any external server except the text you want to embed (sent to your configured LLM proxy for embedding generation).

---

## Use Cases

### Cross-Project Context Sharing
Research or explore a topic in one project, memorize the key findings, then recall that context in a completely different project. No more re-explaining background information to your AI assistant every time you switch contexts.

### Centralized Conversation Memory
Build a centralized knowledge base of key insights from your AI conversations across multiple chat sessions and projects. Instead of losing valuable context in chat history, preserve and organize knowledge that your AI can draw from at any time.

### Saving Examples
Store code snippets, patterns, or worked examples that you want to reuse. Recall them later to guide your AI assistant when working on similar tasks — effectively building your own personal example library.

---

## Prerequisites

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/) package manager
- An LLM proxy that supports the `/embeddings` endpoint (compatible with the OpenAI embeddings API format), using the `text-embedding-005` model

---

## Installation

1. **Clone the repository**

   ```sh
   git clone https://github.com/Razz99/chat-memory.git
   cd chat-memory
   ```

2. **Install dependencies**

   ```sh
   uv sync
   ```

3. **Set environment variables**

   ```sh
   export LLM_PROXY_BASE_URL="https://your-llm-proxy.example.com"
   export LLM_PROXY_API_KEY="your-api-key"
   ```

   Optionally, set a custom database path (defaults to `~/.chat-memory/memories.db`):

   ```sh
   export CHAT_MEMORY_DB_PATH="/path/to/your/memories.db"
   ```

---

## Running the Server

```sh
uv run main.py
```

The server runs over **stdio** and is intended to be used as an MCP server with a compatible AI client (e.g. Copilot, Cursor, or any MCP-compatible host).

---

## Connecting to Your AI Client

### VS Code (GitHub Copilot)

Create a `.vscode/mcp.json` file in your project root:

```json
{
  "servers": {
    "chat-memory": {
      "command": "uv",
      "args": ["run", "/path/to/chat-memory/main.py"],
      "env": {
        "LLM_PROXY_BASE_URL": "https://your-llm-proxy.example.com",
        "LLM_PROXY_API_KEY": "your-api-key"
      }
    }
  }
}
```

---

## Available Tools

Once connected, your AI assistant will have access to the following memory tools:

| Tool | What it does |
|---|---|
| `memorize` | Saves a conversation or summary to memory, tagged by project |
| `recall` | Finds the most relevant memory for a given query and project |
| `recall_by_id` | Retrieves a specific memory by its ID |
| `override_memory` | Updates an existing memory with new content |

### Example prompts you can use with your AI

- *"Summarize this conversation and memorize it."*
- *"Summarize the conversation so far and recall if you remember relevant information"*
- *"Summarize this conversation and update memory #3"*
- *"Recall memory #3 and help me do this task"*

---

## Data Storage

Memories are stored locally in a SQLite database at `~/.chat-memory/memories.db` by default. Each memory is associated with a **project name**, so you can maintain separate memory spaces for different projects.

---

## Verifying Your Setup

To confirm that the `sqlite-vec` extension is working correctly on your system:

```sh
uv run test_sqlite_vec_extension.py
```

You should see output like:

```
True
vec_version=v0.1.x
```

---

## Building a Standalone Binary

If you'd prefer a single executable instead of running via `uv`:

```sh
uv run pyinstaller chat-memory.spec
```

The binary will be output to the `dist/` directory. You can then reference the binary directly in your MCP client configuration instead of using `uv run`.

---

## License

MIT