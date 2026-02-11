#!/usr/bin/env python3
# backend/scripts/embed_chunks.py
# Purpose: Backfill embedding column on knowledge_chunks (one-time, idempotent)
# NOT for: Runtime embedding (that's embedding_service.py)
#
# Usage: cd backend && python scripts/embed_chunks.py
# Cost: $0 — uses free HuggingFace Inference API (BAAI/bge-small-en-v1.5, 384 dims)

import sys
import os
import time

# WHY: Add parent dir to path so we can import config and services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings
from services.embedding_service import get_embeddings_batch_sync, EMBEDDING_DIM

# WHY: Small batches + slow pace — CF Workers AI free tier has strict per-minute rate limits
BATCH_SIZE = 5

engine = create_engine(settings.database_url, pool_pre_ping=True)
Session = sessionmaker(bind=engine)


def embed_all_chunks():
    """Fetch chunks without embeddings, embed in batches, update DB."""
    db = Session()
    try:
        total = db.execute(text(
            "SELECT COUNT(*) FROM knowledge_chunks WHERE embedding IS NULL"
        )).scalar()
        print(f"Chunks to embed: {total} (dim={EMBEDDING_DIM})")

        if total == 0:
            print("All chunks already have embeddings. Nothing to do.")
            return

        done = 0
        while True:
            rows = db.execute(text(
                "SELECT id, content FROM knowledge_chunks "
                "WHERE embedding IS NULL ORDER BY id LIMIT :batch"
            ), {"batch": BATCH_SIZE}).fetchall()

            if not rows:
                break

            ids = [r[0] for r in rows]
            # WHY: Truncate long chunks — bge-small has 512 token limit (~2000 chars)
            texts = [r[1][:2000] for r in rows]

            try:
                embeddings = get_embeddings_batch_sync(texts)
            except Exception as e:
                err = str(e)
                print(f"ERROR on batch starting at id={ids[0]}: {err}")
                # WHY: CF Workers AI has transient 500s, 429 rate limits, and 503 cold starts
                if "500" in err:
                    print("Transient CF error. Waiting 10s...")
                    time.sleep(10)
                    continue
                if "503" in err or "loading" in err.lower():
                    print("Model loading. Waiting 20s...")
                    time.sleep(20)
                    continue
                if "429" in err or "rate" in err.lower():
                    print("Rate limited. Waiting 60s...")
                    time.sleep(60)
                    continue
                raise

            for chunk_id, emb in zip(ids, embeddings):
                emb_str = "[" + ",".join(str(x) for x in emb) + "]"
                db.execute(
                    text("UPDATE knowledge_chunks SET embedding = CAST(:emb AS vector) WHERE id = :id"),
                    {"emb": emb_str, "id": chunk_id},
                )

            db.commit()
            done += len(rows)
            print(f"Embedded {done}/{total} chunks")

            # WHY: CF Workers AI free tier ~10 req/min — 6s between batches to avoid 429
            time.sleep(6.0)

        print(f"Done. Total embedded: {done}")
    finally:
        db.close()


if __name__ == "__main__":
    embed_all_chunks()
