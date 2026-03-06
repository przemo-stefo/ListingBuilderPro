#!/usr/bin/env python3
# backend/scripts/embed_missing_chunks.py
# Purpose: Embed all knowledge_chunks that have embedding IS NULL
# NOT for: Ingestion — only embedding already-ingested chunks

"""
Usage:
    cd listing_builder/backend
    python scripts/embed_missing_chunks.py                    # embed all missing
    python scripts/embed_missing_chunks.py --source kaufland  # only specific source keyword
    python scripts/embed_missing_chunks.py --dry-run          # preview counts only
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings

EMBED_BATCH = 5
SLEEP_BETWEEN = 4.0  # WHY: CF free tier rate limits — 4s between batches


def main():
    dry_run = "--dry-run" in sys.argv
    source_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--source"):
            idx = sys.argv.index(arg)
            if idx + 1 < len(sys.argv):
                source_filter = sys.argv[idx + 1]

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    db = Session()

    # WHY: Show what needs embedding, grouped by source
    if source_filter:
        count_query = text(
            "SELECT source, COUNT(*) FROM knowledge_chunks "
            "WHERE embedding IS NULL AND source ILIKE :filt "
            "GROUP BY source ORDER BY COUNT(*) DESC"
        )
        rows = db.execute(count_query, {"filt": f"%{source_filter}%"}).fetchall()
    else:
        count_query = text(
            "SELECT source, COUNT(*) FROM knowledge_chunks "
            "WHERE embedding IS NULL "
            "GROUP BY source ORDER BY COUNT(*) DESC"
        )
        rows = db.execute(count_query).fetchall()

    total_missing = sum(r[1] for r in rows)
    print(f"Chunks needing embeddings: {total_missing}")
    for r in rows:
        print(f"  {r[0]}: {r[1]}")

    if dry_run or total_missing == 0:
        if dry_run:
            print("\nDry run — nothing embedded.")
        else:
            print("\nAll chunks already have embeddings.")
        db.close()
        return

    from services.embedding_service import get_embeddings_batch_sync, EMBEDDING_DIM
    print(f"\nEmbedding dim: {EMBEDDING_DIM}")
    print(f"Batch size: {EMBED_BATCH}, sleep: {SLEEP_BETWEEN}s\n")

    done = 0
    errors = 0
    while True:
        if source_filter:
            fetch_query = text(
                "SELECT id, content FROM knowledge_chunks "
                "WHERE embedding IS NULL AND source ILIKE :filt "
                "ORDER BY id LIMIT :batch"
            )
            batch_rows = db.execute(fetch_query, {
                "filt": f"%{source_filter}%", "batch": EMBED_BATCH
            }).fetchall()
        else:
            fetch_query = text(
                "SELECT id, content FROM knowledge_chunks "
                "WHERE embedding IS NULL ORDER BY id LIMIT :batch"
            )
            batch_rows = db.execute(fetch_query, {"batch": EMBED_BATCH}).fetchall()

        if not batch_rows:
            break

        ids = [r[0] for r in batch_rows]
        texts = [r[1][:2000] for r in batch_rows]

        try:
            embeddings = get_embeddings_batch_sync(texts)
        except Exception as e:
            err = str(e)
            print(f"  ERROR at id={ids[0]}: {err[:120]}")
            errors += 1
            if any(code in err for code in ["500", "502", "408", "503"]):
                time.sleep(15)
                continue
            if "429" in err or "rate" in err.lower():
                time.sleep(60)
                continue
            if errors > 5:
                print("Too many errors, stopping.")
                break
            time.sleep(10)
            continue

        for chunk_id, emb in zip(ids, embeddings):
            emb_str = "[" + ",".join(str(x) for x in emb) + "]"
            db.execute(
                text("UPDATE knowledge_chunks SET embedding = CAST(:emb AS vector) WHERE id = :id"),
                {"emb": emb_str, "id": chunk_id},
            )

        db.commit()
        done += len(batch_rows)
        if done % 25 == 0 or done >= total_missing:
            print(f"  Embedded {done}/{total_missing} ({done*100//total_missing}%)")
        time.sleep(SLEEP_BETWEEN)

    db.close()
    print(f"\nDone! Embedded {done} chunks. Errors: {errors}")


if __name__ == "__main__":
    main()
