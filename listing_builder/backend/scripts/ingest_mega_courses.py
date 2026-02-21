#!/usr/bin/env python3
# backend/scripts/ingest_mega_courses.py
# Purpose: Ingest 5 MEGA course transcripts into knowledge_chunks for RAG expansion
# NOT for: Runtime — run once from dev machine

"""
Usage:
    cd listing_builder/backend
    python scripts/ingest_mega_courses.py           # ingest + embed
    python scripts/ingest_mega_courses.py --dry-run  # preview only
    python scripts/ingest_mega_courses.py --no-embed  # ingest without embeddings

All 52 MEGA courses (~3,067 transcripts). ON CONFLICT DO NOTHING = safe to re-run.
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
SOURCE_TAG = "mega_course"
MEGA_BASE = os.path.expanduser("~/Documents/MegaTranscripts")

# WHY: All 52 courses from MEGA transcripts. ON CONFLICT DO NOTHING = idempotent.
# Already ingested courses will be skipped automatically.
COURSES = [
    # === BATCH 1 (already ingested — will be skipped) ===
    {"dir": "Stefan Georgi - RMBC II", "source_type": "georgi_rmbc", "prefix": "Georgi RMBC", "default_category": "copywriting"},
    {"dir": "BASHERSFORLIFE - Ecom Talent - The Creative Systems That Print 100K per Day in E", "source_type": "ecom_talent", "prefix": "Ecom Talent", "default_category": "creative_strategy"},
    {"dir": "Barry Hott Building Ads 20", "source_type": "barry_hott_ads", "prefix": "Barry Hott", "default_category": "ad_creative"},
    {"dir": "Daniel Throssell - Market Detective", "source_type": "throssell_market", "prefix": "Throssell", "default_category": "market_research"},
    {"dir": "Russel Brunson conversation domination", "source_type": "brunson_funnels", "prefix": "Brunson", "default_category": "funnels"},
    # === COPYWRITING & SALES ===
    {"dir": "Premium Ghostwriting Academy by Dickie Bush and Nicholas Cole Full Stack Writer ", "source_type": "ghostwriting_academy", "prefix": "Ghostwriting", "default_category": "copywriting"},
    {"dir": "Chris Orzechowski - One Person Agency", "source_type": "orzechowski", "prefix": "Orzechowski", "default_category": "copywriting"},
    {"dir": "Ben Settle - Client-less Copywriter", "source_type": "ben_settle", "prefix": "Settle", "default_category": "copywriting"},
    {"dir": "Kim Krause Schwalm - Supplement Copy Boot Camp", "source_type": "schwalm_supplement", "prefix": "Schwalm", "default_category": "copywriting"},
    {"dir": "Jon Benson ChatVSL Create and even sell high-converting VSLs using only ChatGPT", "source_type": "benson_chatvsl", "prefix": "Benson VSL", "default_category": "copywriting"},
    {"dir": "Frank Kern - Five Courses Bundle", "source_type": "frank_kern", "prefix": "Kern", "default_category": "funnels"},
    # === ADS & CREATIVE ===
    {"dir": "Creative Vibe Marketing with AI AI UGC for Pros Course", "source_type": "creative_vibe_ugc", "prefix": "Creative Vibe", "default_category": "ad_creative"},
    {"dir": "TMS Media - Engaging Ads Academy", "source_type": "tms_engaging_ads", "prefix": "TMS Ads", "default_category": "ad_creative"},
    {"dir": "The Ad Creative course by Fraser Cottrell", "source_type": "cottrell_ad_creative", "prefix": "Cottrell", "default_category": "ad_creative"},
    {"dir": "BASHERSFORLIFE BFL- Sam O Halloran - Scale With Paid Ads In 2025 Info Product Ad", "source_type": "ohalloran_paid_ads", "prefix": "OHalloran", "default_category": "ppc"},
    {"dir": "Philipp Humm - Power of StorySelling", "source_type": "humm_storyselling", "prefix": "Humm", "default_category": "marketing_psychology"},
    # === CONTENT & YOUTUBE ===
    {"dir": "Bryan Ng - YouTube Script Academy BFL", "source_type": "bryan_ng_youtube", "prefix": "Bryan Ng", "default_category": "content_creation"},
    {"dir": "The Client Magnets BASHERS FOR LIFE1", "source_type": "client_magnets_1", "prefix": "Client Magnets", "default_category": "content_creation"},
    {"dir": "The Client Magnets BASHERS FOR LIFE", "source_type": "client_magnets_2", "prefix": "Client Magnets 2", "default_category": "content_creation"},
    {"dir": "Sean Cannell - Video Success Secrets Bonus", "source_type": "cannell_video_1", "prefix": "Cannell", "default_category": "content_creation"},
    {"dir": "Sean Cannell - Video Success Secrets Vol II", "source_type": "cannell_video_2", "prefix": "Cannell V2", "default_category": "content_creation"},
    {"dir": "Ross Harkness - MasteryOS", "source_type": "harkness_mastery", "prefix": "Harkness", "default_category": "content_creation"},
    {"dir": "Zita Viral Content Creator AI Automation 2024 19700 moneyvipprogramcom", "source_type": "zita_viral", "prefix": "Zita", "default_category": "content_creation"},
    # === MARKETING & BUSINESS ===
    {"dir": "Augment - The Augment MBA", "source_type": "augment_mba", "prefix": "Augment MBA", "default_category": "business"},
    {"dir": "Smart Marketer - Smart Business Exit", "source_type": "smart_marketer", "prefix": "Smart Marketer", "default_category": "business"},
    {"dir": "Eddie Cumberbatch - Creator Accelerator", "source_type": "cumberbatch_creator", "prefix": "Cumberbatch", "default_category": "content_creation"},
    {"dir": "Nero Knowledge - The Awakened Entrepreneurs Blueprint v20", "source_type": "nero_knowledge", "prefix": "Nero", "default_category": "business"},
    {"dir": "BASHERSFORLIFE - Alex Hormozi 18k Upsell - ACQ Scale Advisory", "source_type": "hormozi_acq", "prefix": "Hormozi ACQ", "default_category": "business"},
    # === AI & AUTOMATION ===
    {"dir": "Stephen G Pope - NO CODES ARCHITECT 2025 VERSION UPDATED - AI AGENTS AUTOMATION", "source_type": "pope_nocode", "prefix": "Pope NoCode", "default_category": "ai_tools"},
    {"dir": "Corbin ai - Start a Successful AI Automation Agency", "source_type": "corbin_ai", "prefix": "Corbin AI", "default_category": "ai_tools"},
    {"dir": "Niko x Studios - The AI Atelier", "source_type": "niko_ai_atelier", "prefix": "Niko AI", "default_category": "ai_tools"},
    {"dir": "Automation Tribe", "source_type": "automation_tribe", "prefix": "AutoTribe", "default_category": "ai_tools"},
    # === AGENCY & OUTREACH ===
    {"dir": "BASHERSFORLIFE - WisdomElites-Agency Flywheel Accelerator - Faris Bio", "source_type": "agency_flywheel", "prefix": "Flywheel", "default_category": "agency"},
    {"dir": "BASHERS FOR LIFE - Ty Frankel - Sign 2-5 high-ticket clients a month on LinkedIn", "source_type": "frankel_linkedin", "prefix": "Frankel", "default_category": "outreach"},
    {"dir": "Yassin Baum - AI Cold Email Academy", "source_type": "baum_cold_email", "prefix": "Baum", "default_category": "outreach"},
    {"dir": "James Lawrence - Finding A Offers High Ticket Sales", "source_type": "lawrence_sales", "prefix": "Lawrence", "default_category": "sales"},
    {"dir": "Adil Maf - Payment Processing Secrets", "source_type": "maf_payments", "prefix": "Maf", "default_category": "business"},
    {"dir": "Beyond_TheHorizon Sean Ferres - CMB 20 10 Week Fire Your Boss Challenge", "source_type": "beyond_horizon", "prefix": "Beyond", "default_category": "business"},
    {"dir": "Carl Allen - Dealmaker CEO 2021", "source_type": "carl_allen", "prefix": "Allen", "default_category": "business"},
    # === TRADING & FINANCE ===
    {"dir": "The Wall Street Quants BootCamp", "source_type": "quants_bootcamp", "prefix": "Quants", "default_category": "trading"},
    {"dir": "OrderFlows - Crypto Order Flow Trading Course - Mike Valtos", "source_type": "orderflows_crypto", "prefix": "OrderFlows", "default_category": "trading"},
    {"dir": "ALGOHUB 2023 Full Completed", "source_type": "algohub", "prefix": "AlgoHub", "default_category": "trading"},
    {"dir": "WD Gann Secrets Revealed", "source_type": "gann_secrets", "prefix": "Gann", "default_category": "trading"},
    {"dir": "QuantProgram - Prometheus", "source_type": "quantprogram", "prefix": "QuantProg", "default_category": "trading"},
    {"dir": "Trading Busters - London Strategy", "source_type": "trading_busters", "prefix": "TradBust", "default_category": "trading"},
    {"dir": "AlgoTrading101", "source_type": "algotrading101", "prefix": "AlgoTrad", "default_category": "trading"},
    # === OTHER ===
    {"dir": "GSFU", "source_type": "gsfu", "prefix": "GSFU", "default_category": "general"},
    {"dir": "1stman - Outlier Male Body Language", "source_type": "body_language", "prefix": "1stMan", "default_category": "general"},
]

# WHY: Map filename keywords to categories for better RAG filtering
CATEGORY_RULES = [
    # Copywriting & listing
    (r"headline|hook|subject.?line|curiosity|fascination", "copywriting"),
    (r"bullet|feature|benefit|fab\b", "listing_optimization"),
    (r"title|h1|headline", "listing_optimization"),
    (r"description|copy|write|script", "copywriting"),
    (r"vsl|video.?sales|sales.?letter", "copywriting"),
    (r"rmbc|run.?move|block.?close|mechanism", "copywriting"),
    # Ads & creative
    (r"ad\b|ads\b|creative|ugc|visual|image|video.?ad", "ad_creative"),
    (r"hook|angle|pattern.?interrupt", "ad_creative"),
    (r"testing|split|ab.?test|variant", "ad_creative"),
    (r"facebook|meta|instagram|tiktok|social", "ad_creative"),
    (r"sponsored|ppc|campaign|bid|acos", "ppc"),
    # Conversion & psychology
    (r"conversion|convert|checkout|cart|buy", "conversion_optimization"),
    (r"objection|faq|overcome|handle", "conversion_optimization"),
    (r"urgency|scarcity|deadline|fomo", "conversion_optimization"),
    (r"psycholog|persuasi|influence|trigger", "marketing_psychology"),
    (r"story|narrative|origin|founder", "marketing_psychology"),
    # Market research
    (r"research|market|audience|persona|avatar", "market_research"),
    (r"competitor|spy|reverse.?engineer|swipe", "market_research"),
    (r"review|testimonial|voice.?of.?customer|voc", "market_research"),
    (r"niche|segment|target|ideal.?customer", "market_research"),
    # Keywords & ranking
    (r"keyword|seo|rank|search|index", "keyword_research"),
    (r"algorithm|a9|cosmo|ranking", "ranking"),
    # Funnels & traffic
    (r"funnel|landing|opt.?in|squeeze|lead", "funnels"),
    (r"traffic|visitor|click|impression", "traffic"),
    (r"email|sequence|autoresponder|newsletter", "email_marketing"),
    (r"launch|pre.?launch|product.?launch", "product_launch"),
    # Offers & pricing
    (r"offer|price|discount|bundle|upsell|downsell", "offers"),
    (r"value.?stack|bonus|guarantee|risk.?reversal", "offers"),
    # Content & YouTube
    (r"youtube|video|thumbnail|subscribe|channel", "content_creation"),
    (r"content|blog|post|article|thread|newsletter", "content_creation"),
    (r"ghostwrit|ghost.?writ|writing.?system|writing.?habit", "copywriting"),
    # AI & automation
    (r"ai\b|artificial|gpt|chatgpt|llm|prompt|automat", "ai_tools"),
    (r"agent|workflow|n8n|zapier|make\.com|no.?code", "ai_tools"),
    # Agency & outreach
    (r"agency|client.?acqui|retainer|freelanc", "agency"),
    (r"outreach|cold.?email|linkedin|inmail|prospect", "outreach"),
    (r"high.?ticket|close|sales.?call|appointment", "sales"),
    # Trading & finance
    (r"trade|trading|stock|crypto|forex|order.?flow", "trading"),
    (r"algo|quant|backtest|strategy|indicator", "trading"),
    # Business
    (r"business|entrepreneur|startup|scale|exit|acquisition", "business"),
    (r"mindset|productivity|habit|morning|routine", "business"),
]


def detect_category(filename: str, folder_path: str, default: str) -> str:
    """Map filename + folder to category. Falls back to course default."""
    combined = f"{folder_path}/{filename}".lower()
    for pattern, category in CATEGORY_RULES:
        if re.search(pattern, combined):
            return category
    return default


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


def sanitize_filename(name: str, max_len: int = 80) -> str:
    """Create a safe filename for DB unique constraint."""
    return re.sub(r'[^a-zA-Z0-9_-]', '', name.replace(' ', '_'))[:max_len]


def find_transcripts(course_dir: str) -> list[tuple[str, str]]:
    """Find all .txt files in course dir. Returns (full_path, relative_path)."""
    results = []
    for root, _, files in os.walk(course_dir):
        for f in sorted(files):
            if f.endswith('.txt'):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, course_dir)
                results.append((full, rel))
    return results


def main():
    dry_run = "--dry-run" in sys.argv
    no_embed = "--no-embed" in sys.argv

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    db = Session()

    # WHY: Check current state before inserting
    existing = db.execute(text(
        "SELECT COUNT(*) FROM knowledge_chunks WHERE source = :src"
    ), {"src": SOURCE_TAG}).scalar()
    print(f"Existing '{SOURCE_TAG}' chunks: {existing}")

    total_files = 0
    total_chunks = 0
    inserted = 0
    skipped_small = 0
    stats_by_course = {}
    stats_by_category = {}

    for course in COURSES:
        course_dir = os.path.join(MEGA_BASE, course["dir"])
        if not os.path.isdir(course_dir):
            print(f"WARNING: Not found: {course_dir}")
            continue

        transcripts = find_transcripts(course_dir)
        print(f"\n{'='*60}")
        print(f"{course['prefix']}: {len(transcripts)} files in {course['dir']}")
        print(f"{'='*60}")

        course_chunks = 0

        for file_idx, (full_path, rel_path) in enumerate(transcripts):
            basename = os.path.splitext(os.path.basename(rel_path))[0]

            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()

            # WHY: Skip tiny/empty transcripts (likely failed transcriptions)
            if len(content) < 100:
                skipped_small += 1
                continue

            category = detect_category(basename, rel_path, course["default_category"])
            chunks = chunk_text(content)

            # WHY: filename = course prefix + sanitized basename for uniqueness
            db_filename = f"{sanitize_filename(course['prefix'])}_{sanitize_filename(basename)}"

            for chunk_idx, chunk in enumerate(chunks):
                # WHY: Prepend course + lesson context for better RAG retrieval
                chunk_with_context = f"[{course['prefix']} - {basename}]\n{chunk}"

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
                                "source_type": course["source_type"],
                                "chunk_index": chunk_idx,
                                "source": SOURCE_TAG,
                            },
                        )
                        inserted += 1
                    except Exception as e:
                        print(f"  ERROR {db_filename}[{chunk_idx}]: {e}")

                total_chunks += 1
                course_chunks += 1

                # Track category stats
                stats_by_category[category] = stats_by_category.get(category, 0) + 1

            total_files += 1

            if (file_idx + 1) % 50 == 0:
                if not dry_run:
                    db.commit()
                print(f"  Progress: {file_idx + 1}/{len(transcripts)} files, {course_chunks} chunks")

        if not dry_run:
            db.commit()

        stats_by_course[course["prefix"]] = {
            "files": len(transcripts),
            "chunks": course_chunks,
        }

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY {'(DRY RUN)' if dry_run else ''}")
    print(f"{'='*60}")
    print(f"Files processed: {total_files}")
    print(f"Files skipped (too small): {skipped_small}")
    print(f"Total chunks: {total_chunks}")
    if not dry_run:
        print(f"Inserted to DB: {inserted}")

    print(f"\nBy course:")
    for name, s in stats_by_course.items():
        print(f"  {name}: {s['files']} files → {s['chunks']} chunks")

    print(f"\nBy category:")
    for cat, count in sorted(stats_by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    if dry_run or no_embed:
        if dry_run:
            print("\nDry run — nothing inserted. Remove --dry-run to execute.")
        if no_embed:
            print("\nSkipping embeddings. Run embed_chunks.py separately.")
        db.close()
        return

    # Phase 2: Embed new chunks
    print(f"\n--- Embedding phase ---")
    try:
        from services.embedding_service import get_embeddings_batch_sync, EMBEDDING_DIM
    except ImportError:
        print("WARNING: embedding_service not available. Run embed_chunks.py separately.")
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
        # WHY: CF Workers AI free tier — ~10 req/min, 5 texts/req
        time.sleep(6.0)

    db.close()
    print(f"\nAll done! {done} chunks embedded.")


if __name__ == "__main__":
    main()
