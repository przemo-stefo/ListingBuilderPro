#!/usr/bin/env python3
# backend/scripts/ingest_ecom_creative_transcripts.py
# Purpose: Ingest ecom creative expert transcripts into knowledge_chunks table
# NOT for: Production runtime — run once from dev machine, then archive

"""
Usage:
    cd listing_builder/backend
    python scripts/ingest_bfl_transcripts.py

Expects .env with DATABASE_URL (Supabase PostgreSQL).
Inserts chunks with ON CONFLICT DO NOTHING (idempotent re-runs).
Source: "ecom_creative_expert" — distinct from Inner Circle's "standalone"/"Office_Hours"/etc.
"""

import os
import re
import sys

# WHY: Add backend dir to path so we can import config/database
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings

TRANSCRIPTS_DIR = "/Volumes/Backup_1TB/BashersForLife_transcripts"
CHUNK_SIZE = 1500       # ~500 words at ~3 chars/word
CHUNK_OVERLAP = 200


# WHY: Map filenames to ecom creative categories based on keywords in the name.
# Order matters — first match wins. More specific patterns go first.
CATEGORY_RULES = [
    # Copywriting: scripts + copy for ads (before video/static to catch cross-category)
    (r"write_copy|write_script|copywriting", "copywriting"),
    # Video editing breakdowns + live editing examples
    (r"video_editing|editing_breakdown|live_example_editing", "video_editing"),
    # Static ads (before video_ads so "static_ad_safezone" doesn't match video rule)
    (r"static_ad", "static_ads"),
    # Video ads mastery + video ad types
    (r"video_ads|3va_|video_hook|retention|action_item.*organic|action_item.*high.production", "video_ads"),
    # UGC content
    (r"ugc", "video_ads"),
    # AI tools: image generation, voiceovers, Claude, GenAI, prompt engineering
    (r"ai_product_image|ai_content|ai_voiceover|generate.*image|genai|generative_al|prompt_engineering|claude|karlo_method|tech_stack", "ai_tools"),
    # Creative strategy & ad ideas
    (r"creative_strategy|ad_ideas|ad_bounties|feedback_loop|breaking_down|winning_ad|losing_ad|imitation|ideation|iteration", "creative_strategy"),
    # Marketing psychology: brain, awareness, sophistication, buying psychology, customer
    (r"brain_works|awareness|sophistication|buying_psychology|understanding.*customer|how_do_ads_work|direct_response", "marketing_psychology"),
    # Research & market analysis
    (r"research|deep_market", "creative_strategy"),
    # Brand AI, growth guide
    (r"brand_ai|growth_guide", "ai_tools"),
    # Ad creation process
    (r"ad_creation_process|ad_inspiration", "creative_strategy"),
]


def detect_category(filename: str) -> str:
    """Detect topic category from filename using regex rules."""
    lower = filename.lower()
    for pattern, category in CATEGORY_RULES:
        if re.search(pattern, lower):
            return category
    return "general"


def chunk_text(raw: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into chunks, breaking at sentence boundaries.

    WHY: Same chunking logic as Inner Circle ingest — keeps chunk sizes consistent
    across both knowledge sources for balanced RAG retrieval.
    """
    if len(raw) <= chunk_size:
        return [raw.strip()] if raw.strip() else []

    chunks = []
    start = 0

    while start < len(raw):
        end = start + chunk_size

        if end >= len(raw):
            chunk = raw[start:].strip()
            if chunk:
                chunks.append(chunk)
            break

        # WHY: Find last sentence boundary (. ! ?) before chunk_size limit
        boundary = end
        for i in range(end, max(start + chunk_size // 2, start), -1):
            if raw[i] in ".!?" and i + 1 < len(raw) and raw[i + 1] in " \n":
                boundary = i + 1
                break

        chunk = raw[start:boundary].strip()
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
    print(f"Found {len(txt_files)} ecom creative transcript files")

    # WHY: Preview category assignments before inserting
    print("\nCategory mapping preview:")
    cat_counts: dict[str, int] = {}
    for filename in txt_files:
        cat = detect_category(filename)
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} files")
    print()

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
        # WHY: source_type = "ecom_creative_expert" distinguishes from Inner Circle transcripts
        source_type = "ecom_creative_expert"
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

    # WHY: Verify counts — show BFL-only stats and combined totals
    db2 = Session()

    print("\nEcom creative category breakdown:")
    result = db2.execute(text(
        "SELECT category, COUNT(*) as cnt, COUNT(DISTINCT filename) as files "
        "FROM knowledge_chunks WHERE source_type = 'ecom_creative_expert' "
        "GROUP BY category ORDER BY cnt DESC"
    ))
    for row in result:
        print(f"  {row[0]}: {row[1]} chunks from {row[2]} files")

    print("\nFull knowledge base totals:")
    result = db2.execute(text(
        "SELECT source_type, COUNT(*) as cnt, COUNT(DISTINCT filename) as files "
        "FROM knowledge_chunks GROUP BY source_type ORDER BY cnt DESC"
    ))
    for row in result:
        print(f"  {row[0]}: {row[1]} chunks from {row[2]} files")

    db2.close()


if __name__ == "__main__":
    main()
