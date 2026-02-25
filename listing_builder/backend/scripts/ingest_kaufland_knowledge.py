#!/usr/bin/env python3
# backend/scripts/ingest_kaufland_knowledge.py
# Purpose: Ingest Kaufland marketplace knowledge into knowledge_chunks for RAG
# NOT for: Runtime — run once from dev machine

"""
Usage:
    cd listing_builder/backend
    python scripts/ingest_kaufland_knowledge.py           # ingest + embed
    python scripts/ingest_kaufland_knowledge.py --dry-run  # preview only
    python scripts/ingest_kaufland_knowledge.py --no-embed  # ingest without embeddings

Kaufland knowledge base files. ON CONFLICT DO NOTHING = safe to re-run.
"""

import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
EMBED_BATCH = 5
SOURCE_TAG = "kaufland_knowledge"
SOURCE_TYPE = "kaufland_marketplace"
PREFIX = "Kaufland"
BASE_DIR = os.path.expanduser("~/Documents/KauflandKnowledge")

# WHY: Map section headers to RAG categories for better retrieval
SECTION_CATEGORY = {
    "INFORMACJE OGÓLNE": "kaufland_general",
    "REJESTRACJA": "kaufland_registration",
    "OPŁATY I PROWIZJE": "kaufland_fees",
    "DANYCH PRODUKTOWYCH": "kaufland_product_data",
    "TYTUŁ PRODUKTU": "listing_optimization",
    "OPIS PRODUKTU": "listing_optimization",
    "EAN/GTIN": "kaufland_product_data",
    "ZDJĘCIA": "kaufland_product_data",
    "KATEGORIE": "kaufland_categories",
    "ATRYBUTY": "kaufland_product_data",
    "BUY BOX": "kaufland_buybox",
    "WYSYŁKA": "kaufland_shipping",
    "FULFILLMENT": "kaufland_shipping",
    "OBSŁUGA KLIENTA": "kaufland_customer_service",
    "SEO": "listing_optimization",
    "WIDOCZNOŚĆ": "listing_optimization",
    "BŁĘDY SPRZEDAWCÓW": "kaufland_general",
    "PORÓWNANIE Z AMAZON": "kaufland_general",
    "GPSR": "kaufland_compliance",
    "API KAUFLAND": "kaufland_api",
    "RYNKI KAUFLAND": "kaufland_general",
    "MARKETING": "kaufland_marketing",
}


def detect_category(chunk_text: str) -> str:
    """Detect category from chunk content based on section headers."""
    upper = chunk_text.upper()
    for keyword, category in SECTION_CATEGORY.items():
        if keyword in upper:
            return category
    return "kaufland_general"


def chunk_text(content: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks at section/sentence boundaries."""
    # WHY: First try splitting on section headers (===) for clean breaks
    sections = re.split(r'\n(?====\s)', content)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section or len(section) < 50:
            continue

        if len(section) <= chunk_size:
            chunks.append(section)
            continue

        # Sub-chunk long sections at sentence boundaries
        start = 0
        while start < len(section):
            end = start + chunk_size
            if end >= len(section):
                chunk = section[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            boundary = end
            for i in range(end, max(start + chunk_size // 2, start), -1):
                if section[i] in ".!?\n" and i + 1 < len(section):
                    boundary = i + 1
                    break

            chunk = section[start:boundary].strip()
            if chunk:
                chunks.append(chunk)
            start = boundary - overlap if boundary - overlap > start else boundary

    return chunks


def sanitize_filename(name: str, max_len: int = 80) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '', name.replace(' ', '_'))[:max_len]


def main():
    dry_run = "--dry-run" in sys.argv
    no_embed = "--no-embed" in sys.argv

    if not os.path.isdir(BASE_DIR):
        print(f"ERROR: Directory not found: {BASE_DIR}")
        sys.exit(1)

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    db = Session()

    existing = db.execute(text(
        "SELECT COUNT(*) FROM knowledge_chunks WHERE source = :src"
    ), {"src": SOURCE_TAG}).scalar()
    print(f"Existing '{SOURCE_TAG}' chunks: {existing}")

    files = sorted(f for f in os.listdir(BASE_DIR) if f.endswith(".txt"))
    print(f"Found {len(files)} knowledge files in {BASE_DIR}\n")

    total_chunks = 0
    inserted = 0
    stats_by_category = {}

    for file_idx, filename in enumerate(files):
        filepath = os.path.join(BASE_DIR, filename)
        basename = os.path.splitext(filename)[0]

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()

        if len(content) < 100:
            continue

        chunks = chunk_text(content)
        db_filename = f"{PREFIX}_{sanitize_filename(basename)}"

        for chunk_idx, chunk in enumerate(chunks):
            category = detect_category(chunk)
            chunk_with_context = f"[Kaufland Marketplace - {basename}]\n{chunk}"

            if not dry_run:
                try:
                    db.execute(
                        text("""
                            INSERT INTO knowledge_chunks
                            (content, filename, category, source_type, chunk_index, source)
                            VALUES (:content, :filename, :category, :source_type, :chunk_index, :source)
                            ON CONFLICT (filename, chunk_index) DO NOTHING
                        """),
                        {
                            "content": chunk_with_context,
                            "filename": db_filename,
                            "category": category,
                            "source_type": SOURCE_TYPE,
                            "chunk_index": chunk_idx,
                            "source": SOURCE_TAG,
                        },
                    )
                    inserted += 1
                except Exception as e:
                    print(f"  ERROR {db_filename}[{chunk_idx}]: {e}")

            total_chunks += 1
            stats_by_category[category] = stats_by_category.get(category, 0) + 1

    if not dry_run:
        db.commit()

    print(f"\n{'='*60}")
    print(f"SUMMARY {'(DRY RUN)' if dry_run else ''}")
    print(f"{'='*60}")
    print(f"Files processed: {len(files)}")
    print(f"Total chunks: {total_chunks}")
    if not dry_run:
        print(f"Inserted to DB: {inserted}")

    print(f"\nBy category:")
    for cat, count in sorted(stats_by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    if dry_run or no_embed:
        if dry_run:
            print("\nDry run — nothing inserted. Remove --dry-run to execute.")
        db.close()
        return

    # Phase 2: Embed
    print(f"\n--- Embedding phase ---")
    try:
        from services.embedding_service import get_embeddings_batch_sync, EMBEDDING_DIM
    except ImportError:
        print("WARNING: embedding_service not available.")
        db.close()
        return

    to_embed = db.execute(text(
        "SELECT COUNT(*) FROM knowledge_chunks WHERE source = :src AND embedding IS NULL"
    ), {"src": SOURCE_TAG}).scalar()
    print(f"Chunks to embed: {to_embed} (dim={EMBEDDING_DIM})")

    if to_embed == 0:
        print("All chunks already embedded.")
        db.close()
        return

    done = 0
    while True:
        rows = db.execute(text(
            "SELECT id, content FROM knowledge_chunks "
            "WHERE source = :src AND embedding IS NULL ORDER BY id LIMIT :batch"
        ), {"src": SOURCE_TAG, "batch": EMBED_BATCH}).fetchall()

        if not rows:
            break

        ids = [r[0] for r in rows]
        texts = [r[1][:2000] for r in rows]

        try:
            embeddings = get_embeddings_batch_sync(texts)
        except Exception as e:
            err = str(e)
            print(f"  Embed error at id={ids[0]}: {err[:100]}")
            if any(code in err for code in ["500", "502", "408", "503"]):
                time.sleep(15)
                continue
            if "429" in err or "rate" in err.lower():
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
        if done % 50 == 0 or done == to_embed:
            print(f"  Embedded {done}/{to_embed}")
        time.sleep(6.0)

    db.close()
    print(f"\nAll done! {done} chunks embedded.")


if __name__ == "__main__":
    main()
