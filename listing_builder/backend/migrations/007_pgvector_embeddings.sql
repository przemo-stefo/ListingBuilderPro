-- backend/migrations/007_pgvector_embeddings.sql
-- Purpose: Add pgvector embedding column to knowledge_chunks for hybrid search
-- NOT for: Data ingestion (see scripts/embed_chunks.py)

-- WHY: pgvector extension enables vector similarity search in PostgreSQL
CREATE EXTENSION IF NOT EXISTS vector;

-- WHY: 384 dims = BAAI/bge-small-en-v1.5 via HuggingFace (free, no API key needed)
-- Nullable so existing rows aren't affected — backfilled by embed_chunks.py
ALTER TABLE knowledge_chunks
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- WHY: HNSW index for fast approximate nearest neighbor search
-- m=32 (connections per node) is sufficient for <10K vectors (ChatRAG uses m=64 for larger sets)
-- ef_construction=128 balances build speed vs recall quality
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding
ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 32, ef_construction = 128);

-- Verification:
-- SELECT embedding IS NULL FROM knowledge_chunks LIMIT 1;  -- should be true before embedding
-- SELECT COUNT(*) FROM knowledge_chunks WHERE embedding IS NOT NULL;  -- 0 before, 6587 after
