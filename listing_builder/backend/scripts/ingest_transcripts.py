#!/usr/bin/env python3
# backend/scripts/ingest_transcripts.py
# Purpose: One-time local script to ingest Inner Circle transcripts into Supabase
# NOT for: Production runtime — run once from dev machine, then delete or archive

"""
Usage:
    cd listing_builder/backend
    python scripts/ingest_transcripts.py

Expects SUPABASE_DB_URL env var or reads from .env / config.
Inserts ~7-10K chunks with ON CONFLICT DO NOTHING (idempotent re-runs).
"""

import os
import re
import sys

# WHY: Add backend dir to path so we can import config/database
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings

TRANSCRIPTS_DIR = "/Users/shawn/Projects/akademia-marketplace/.knowledge/transcripts"
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200


def detect_category(filename: str) -> str:
    """Detect topic category from filename keywords."""
    lower = filename.lower()
    if "listing_optimization" in lower:
        return "listing_optimization"
    if "keyword_research" in lower or "keyword" in lower:
        return "keyword_research"
    if "ranking" in lower:
        return "ranking"
    if "ppc" in lower:
        return "ppc"
    if "conversion" in lower:
        return "conversion_optimization"
    if "inventory" in lower:
        return "inventory_management"
    return "general"


def detect_source_type(filename: str) -> str:
    """Detect source type from filename prefix."""
    if filename.startswith("Office_Hours"):
        return "Office_Hours"
    if filename.startswith("Masterclass"):
        return "Masterclass"
    if filename.startswith("Special_Call"):
        return "Special_Call"
    if filename.startswith("PPC_AMA"):
        return "PPC_AMA"
    return "standalone"


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into chunks, breaking at sentence boundaries."""
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break

        # WHY: Find last sentence boundary (. ! ?) before chunk_size limit
        # Look backwards from end position for a sentence-ending punctuation
        boundary = end
        for i in range(end, max(start + chunk_size // 2, start), -1):
            if text[i] in ".!?" and i + 1 < len(text) and text[i + 1] in " \n":
                boundary = i + 1
                break

        chunk = text[start:boundary].strip()
        if chunk:
            chunks.append(chunk)

        # WHY: Overlap ensures context isn't lost at chunk boundaries
        start = boundary - overlap if boundary - overlap > start else boundary

    return chunks


def main():
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    db = Session()

    if not os.path.isdir(TRANSCRIPTS_DIR):
        print(f"ERROR: Transcripts dir not found: {TRANSCRIPTS_DIR}")
        sys.exit(1)

    txt_files = sorted(f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith(".txt"))
    print(f"Found {len(txt_files)} transcript files")

    total_chunks = 0
    inserted = 0
    skipped = 0

    for file_idx, filename in enumerate(txt_files):
        filepath = os.path.join(TRANSCRIPTS_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            print(f"  SKIP (empty): {filename}")
            continue

        category = detect_category(filename)
        source_type = detect_source_type(filename)
        chunks = chunk_text(content)
        total_chunks += len(chunks)

        for chunk_idx, chunk in enumerate(chunks):
            try:
                db.execute(
                    text("""
                        INSERT INTO knowledge_chunks (content, filename, category, source_type, chunk_index)
                        VALUES (:content, :filename, :category, :source_type, :chunk_index)
                        ON CONFLICT (filename, chunk_index) DO NOTHING
                    """),
                    {
                        "content": chunk,
                        "filename": filename,
                        "category": category,
                        "source_type": source_type,
                        "chunk_index": chunk_idx,
                    },
                )
                inserted += 1
            except Exception as e:
                skipped += 1
                print(f"  ERROR inserting {filename}[{chunk_idx}]: {e}")

        if (file_idx + 1) % 20 == 0:
            db.commit()
            print(f"  Progress: {file_idx + 1}/{len(txt_files)} files, {total_chunks} chunks")

    db.commit()
    db.close()

    print(f"\nDone!")
    print(f"  Files processed: {len(txt_files)}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Inserted: {inserted}")
    print(f"  Skipped (dupes/errors): {skipped}")

    # Verify counts by category
    db2 = Session()
    result = db2.execute(text(
        "SELECT category, COUNT(*) as cnt, COUNT(DISTINCT filename) as files "
        "FROM knowledge_chunks GROUP BY category ORDER BY cnt DESC"
    ))
    print("\nCategory breakdown:")
    for row in result:
        print(f"  {row[0]}: {row[1]} chunks from {row[2]} files")
    db2.close()


if __name__ == "__main__":
    main()
