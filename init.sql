-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Store memories with embeddings
CREATE TABLE IF NOT EXISTS memories (
    id          SERIAL PRIMARY KEY,
    project_name  TEXT NOT NULL,
    chat_title  TEXT NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(768), -- text-embedding-005 produces 768-dim vectors
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast ANN (approximate nearest-neighbour) search
CREATE INDEX IF NOT EXISTS memories_embedding_idx
    ON memories
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

