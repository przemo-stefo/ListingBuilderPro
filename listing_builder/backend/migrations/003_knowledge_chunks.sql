-- backend/migrations/003_knowledge_chunks.sql
-- Purpose: Knowledge base table for Inner Circle transcript chunks (tsvector full-text search)
-- NOT for: Embedding-based vector search (we use built-in PostgreSQL FTS instead)

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    filename TEXT NOT NULL,
    category TEXT NOT NULL,          -- keyword_research, ranking, listing_optimization, ppc, conversion_optimization, general
    source_type TEXT NOT NULL,       -- Office_Hours, Masterclass, Special_Call, PPC_AMA, standalone
    chunk_index INT NOT NULL,
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(filename, chunk_index)
);

-- WHY: GIN index makes @@ full-text queries fast (required for tsvector)
CREATE INDEX IF NOT EXISTS idx_knowledge_search ON knowledge_chunks USING GIN(search_vector);

-- WHY: B-tree on category for pre-filtering before FTS
CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_chunks(category);

-- Verification query:
-- SELECT category, COUNT(*) as chunks, COUNT(DISTINCT filename) as files
-- FROM knowledge_chunks GROUP BY category ORDER BY chunks DESC;
