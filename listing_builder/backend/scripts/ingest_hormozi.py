#!/usr/bin/env python3
# backend/scripts/ingest_hormozi.py
# Purpose: Ingest Hormozi transcripts into knowledge_chunks for RAG
# NOT for: Runtime — run once from dev machine

"""
Usage:
    cd listing_builder/backend
    python scripts/ingest_hormozi.py

Reads FULL_TRANSCRIPTS.md, chunks by section headers, inserts with source='hormozi'.
Then runs embedding backfill on new chunks.
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

TRANSCRIPTS_FILE = os.path.expanduser(
    "~/Documents/backups/hormozi-transcripts/FULL_TRANSCRIPTS.md"
)
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
EMBED_BATCH = 5


def chunk_text(content: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks at sentence boundaries."""
    if len(content) <= chunk_size:
        return [content.strip()] if content.strip() else []

    chunks = []
    start = 0
    while start < len(content):
        end = start + chunk_size
        if end >= len(content):
            chunk = content[start:].strip()
            if chunk:
                chunks.append(chunk)
            break

        # WHY: Break at sentence boundary to preserve meaning
        boundary = end
        for i in range(end, max(start + chunk_size // 2, start), -1):
            if content[i] in ".!?\n" and i + 1 < len(content):
                boundary = i + 1
                break

        chunk = content[start:boundary].strip()
        if chunk:
            chunks.append(chunk)
        start = boundary - overlap if boundary - overlap > start else boundary

    return chunks


def detect_category(section_title: str) -> str:
    """Map Hormozi section titles to categories."""
    lower = section_title.lower()
    if "money model" in lower or "offer" in lower:
        return "money_models"
    if "cac" in lower or "acquisition" in lower:
        return "customer_acquisition"
    if "gross profit" in lower or "gp" in lower:
        return "gross_profit"
    if "payback" in lower or "ppd" in lower:
        return "payback_period"
    if "upsell" in lower:
        return "upsell"
    if "downsell" in lower:
        return "downsell"
    if "continuity" in lower:
        return "continuity"
    if "attraction" in lower or "giveaway" in lower or "decoy" in lower:
        return "attraction_offers"
    if "cfa" in lower or "client finance" in lower:
        return "client_finance"
    if "skool" in lower or "tutorial" in lower:
        return "skool_tutorial"
    return "general"


def parse_sections(content: str) -> list[dict]:
    """Split MD file by ## headers into sections with titles."""
    # WHY: Split by ## headers to keep each lesson as a logical unit
    pattern = r'^(#{1,3})\s+(.+?)$'
    sections = []
    current_title = "Introduction"
    current_text = []

    for line in content.split('\n'):
        match = re.match(pattern, line)
        if match and len(match.group(1)) <= 3:
            # Save previous section
            text_block = '\n'.join(current_text).strip()
            if text_block and len(text_block) > 50:
                sections.append({
                    'title': current_title,
                    'text': text_block
                })
            current_title = match.group(2).strip()
            current_text = []
        else:
            current_text.append(line)

    # Last section
    text_block = '\n'.join(current_text).strip()
    if text_block and len(text_block) > 50:
        sections.append({'title': current_title, 'text': text_block})

    return sections


def main():
    if not os.path.isfile(TRANSCRIPTS_FILE):
        print(f"ERROR: File not found: {TRANSCRIPTS_FILE}")
        sys.exit(1)

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    db = Session()

    print(f"Reading: {TRANSCRIPTS_FILE}")
    with open(TRANSCRIPTS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"File size: {len(content):,} chars")

    # Parse into sections by headers
    sections = parse_sections(content)
    print(f"Sections found: {len(sections)}")

    total_chunks = 0
    inserted = 0

    for sec_idx, section in enumerate(sections):
        category = detect_category(section['title'])
        chunks = chunk_text(section['text'])

        # WHY: Use section title as filename prefix for unique constraint
        filename = f"hormozi_{sec_idx:03d}_{section['title'][:60].replace(' ', '_')}"
        # Sanitize filename
        filename = re.sub(r'[^a-zA-Z0-9_-]', '', filename)

        for chunk_idx, chunk in enumerate(chunks):
            # WHY: Prepend section title to chunk for better RAG retrieval
            chunk_with_context = f"[Hormozi - {section['title']}]\n{chunk}"
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
                        "filename": filename,
                        "category": category,
                        "source_type": "hormozi_transcript",
                        "chunk_index": chunk_idx,
                        "source": "hormozi",
                    },
                )
                inserted += 1
            except Exception as e:
                print(f"  ERROR {filename}[{chunk_idx}]: {e}")

            total_chunks += 1

        if (sec_idx + 1) % 10 == 0:
            db.commit()
            print(f"  Progress: {sec_idx + 1}/{len(sections)} sections, {total_chunks} chunks")

    db.commit()
    print(f"\nIngestion done!")
    print(f"  Sections: {len(sections)}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Inserted: {inserted}")

    # Phase 2: Embed new chunks
    print(f"\n--- Embedding phase ---")
    try:
        from services.embedding_service import get_embeddings_batch_sync, EMBEDDING_DIM
    except ImportError:
        print("WARNING: embedding_service not available. Run embed_chunks.py separately.")
        db.close()
        return

    to_embed = db.execute(text(
        "SELECT COUNT(*) FROM knowledge_chunks WHERE source = 'hormozi' AND embedding IS NULL"
    )).scalar()
    print(f"Chunks to embed: {to_embed} (dim={EMBEDDING_DIM})")

    if to_embed == 0:
        print("All Hormozi chunks already embedded.")
        db.close()
        return

    done = 0
    while True:
        rows = db.execute(text(
            "SELECT id, content FROM knowledge_chunks "
            "WHERE source = 'hormozi' AND embedding IS NULL ORDER BY id LIMIT :batch"
        ), {"batch": EMBED_BATCH}).fetchall()

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
        print(f"  Embedded {done}/{to_embed}")
        # WHY: CF Workers AI free tier rate limits
        time.sleep(6.0)

    db.close()
    print(f"\nAll done! {done} chunks embedded.")


if __name__ == "__main__":
    main()
