#!/usr/bin/env python3
# /Users/shawn/Projects/ListingBuilderPro/listing_builder/viral_learning.py
# Purpose: AI-powered viral pattern learning system with Qdrant vector DB
# NOT for: Production without proper API keys and persistence setup

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import sqlite3
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

app = FastAPI(title="Viral Pattern Learning API")

# Qdrant setup - in-memory for simplicity (can switch to server mode)
QDRANT_PATH = os.path.expanduser("~/.qdrant_viral_patterns")
qdrant = QdrantClient(path=QDRANT_PATH)

COLLECTION_NAME = "viral_patterns"
VECTOR_SIZE = 384  # Size for all-MiniLM-L6-v2 model

# Groq API for embeddings alternative (using their models)
GROQ_API_KEY = None

def get_groq_key():
    """Get Groq API key from secrets"""
    global GROQ_API_KEY
    if GROQ_API_KEY:
        return GROQ_API_KEY
    try:
        with open(os.path.expanduser("~/.claude/secrets.md"), "r") as f:
            content = f.read()
            import re
            match = re.search(r'gsk_[a-zA-Z0-9]+', content)
            if match:
                GROQ_API_KEY = match.group(0)
                return GROQ_API_KEY
    except:
        pass
    return None

# Use sentence-transformers for embeddings (free, local)
_model = None
def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def get_embedding(text: str) -> List[float]:
    """Get embedding vector for text using local model"""
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()

def ensure_collection():
    """Create collection if it doesn't exist"""
    collections = qdrant.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)

    if not exists:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        print(f"Created collection: {COLLECTION_NAME}")
    return True

class PatternInput(BaseModel):
    video_id: str
    title: str
    hook: str
    hook_type: str
    why_viral: str
    transcript: Optional[str] = ""

class TopicQuery(BaseModel):
    topic: str
    niche: Optional[str] = "general"
    limit: int = 5

class HookRequest(BaseModel):
    topic: str
    style: Optional[str] = None  # e.g., "MrBeast", "educational", "fear"
    limit: int = 3

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    ensure_collection()
    # Load existing patterns from SQLite
    await load_patterns_from_db()

async def load_patterns_from_db():
    """Load existing viral patterns from n8n database"""
    db_path = os.path.expanduser("~/.n8n/database.sqlite")
    if not os.path.exists(db_path):
        print("n8n database not found")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT videoId, title, hook, hookType, whyViral, transcript
            FROM data_table_user_UuYaMMFqvzvTQWPX
            WHERE title IS NOT NULL AND title != ''
        """)
        rows = cursor.fetchall()

        # Check current count in Qdrant
        info = qdrant.get_collection(COLLECTION_NAME)
        current_count = info.points_count

        if len(rows) > current_count:
            print(f"Loading {len(rows) - current_count} new patterns into Qdrant...")

            points = []
            for i, row in enumerate(rows):
                video_id, title, hook, hook_type, why_viral, transcript = row

                # Create rich text for embedding
                text_for_embedding = f"""
                Title: {title or ''}
                Hook: {hook or ''}
                Hook Type: {hook_type or ''}
                Why Viral: {why_viral or ''}
                """.strip()

                if not text_for_embedding or len(text_for_embedding) < 10:
                    continue

                embedding = get_embedding(text_for_embedding)

                points.append(PointStruct(
                    id=i,
                    vector=embedding,
                    payload={
                        "video_id": video_id or "",
                        "title": title or "",
                        "hook": hook or "",
                        "hook_type": hook_type or "",
                        "why_viral": why_viral or "",
                        "transcript": (transcript or "")[:500]
                    }
                ))

            if points:
                # Recreate collection with fresh data
                qdrant.delete_collection(COLLECTION_NAME)
                ensure_collection()
                qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
                print(f"Loaded {len(points)} patterns into Qdrant")

    except Exception as e:
        print(f"Error loading patterns: {e}")
    finally:
        conn.close()

@app.get("/health")
def health():
    """Health check"""
    info = qdrant.get_collection(COLLECTION_NAME)
    return {
        "status": "ok",
        "collection": COLLECTION_NAME,
        "patterns_count": info.points_count
    }

@app.post("/learn")
async def learn_pattern(pattern: PatternInput):
    """Add a new pattern to the learning database"""
    ensure_collection()

    # Create embedding from pattern data
    text_for_embedding = f"""
    Title: {pattern.title}
    Hook: {pattern.hook}
    Hook Type: {pattern.hook_type}
    Why Viral: {pattern.why_viral}
    """.strip()

    embedding = get_embedding(text_for_embedding)

    # Get next ID
    info = qdrant.get_collection(COLLECTION_NAME)
    next_id = info.points_count

    # Store in Qdrant
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(
            id=next_id,
            vector=embedding,
            payload={
                "video_id": pattern.video_id,
                "title": pattern.title,
                "hook": pattern.hook,
                "hook_type": pattern.hook_type,
                "why_viral": pattern.why_viral,
                "transcript": pattern.transcript[:500] if pattern.transcript else ""
            }
        )]
    )

    return {"success": True, "message": "Pattern learned", "id": next_id}

@app.post("/search")
async def search_similar(query: TopicQuery):
    """Find similar viral patterns for a topic"""
    ensure_collection()

    # Create embedding for the query
    query_text = f"Topic: {query.topic}. Niche: {query.niche}"
    query_embedding = get_embedding(query_text)

    # Search Qdrant (v1.16+ API uses query_points)
    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=query.limit
    )

    patterns = []
    for result in results.points:
        patterns.append({
            "score": result.score,
            "video_id": result.payload.get("video_id"),
            "title": result.payload.get("title"),
            "hook": result.payload.get("hook"),
            "hook_type": result.payload.get("hook_type"),
            "why_viral": result.payload.get("why_viral")
        })

    return {
        "success": True,
        "query": query.topic,
        "similar_patterns": patterns
    }

@app.post("/suggest-hooks")
async def suggest_hooks(request: HookRequest):
    """Generate hook suggestions based on topic and learned patterns"""
    ensure_collection()

    # Find similar patterns
    query_text = f"Topic: {request.topic}"
    if request.style:
        query_text += f" Style: {request.style}"

    query_embedding = get_embedding(query_text)

    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=5
    )

    if not results.points:
        return {"success": False, "message": "No patterns in database yet"}

    # Collect relevant hooks and types
    relevant_hooks = []
    hook_types_count = {}

    for result in results.points:
        hook = result.payload.get("hook", "")
        hook_type = result.payload.get("hook_type", "")
        why_viral = result.payload.get("why_viral", "")

        if hook:
            relevant_hooks.append({
                "original_hook": hook,
                "hook_type": hook_type,
                "why_worked": why_viral,
                "similarity": result.score
            })

        if hook_type:
            hook_types_count[hook_type] = hook_types_count.get(hook_type, 0) + 1

    # Determine best hook type for this topic
    best_hook_type = max(hook_types_count, key=hook_types_count.get) if hook_types_count else "curiosity_gap"

    # Generate suggestions using Groq
    groq_key = get_groq_key()
    suggestions = []

    if groq_key:
        try:
            # Build context from similar hooks
            hooks_context = "\n".join([
                f"- Hook: \"{h['original_hook']}\" (Type: {h['hook_type']})"
                for h in relevant_hooks[:3]
            ])

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a viral content expert. Generate hooks that grab attention in the first 3 seconds. Be specific and actionable."
                        },
                        {
                            "role": "user",
                            "content": f"""Based on these successful viral hooks:
{hooks_context}

Generate 3 NEW hooks for this topic: "{request.topic}"
Best hook type for this topic: {best_hook_type}

Rules:
- Each hook should be 1-2 sentences max
- Use the {best_hook_type} style
- Make them specific to the topic
- Include numbers or specific claims when possible

Return as JSON array: [{{"hook": "...", "hook_type": "...", "why_works": "..."}}]"""
                        }
                    ],
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"}
                },
                timeout=30
            )

            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            parsed = json.loads(content)

            # Handle different response formats
            if isinstance(parsed, list):
                suggestions = parsed
            elif isinstance(parsed, dict) and "hooks" in parsed:
                suggestions = parsed["hooks"]
            elif isinstance(parsed, dict):
                suggestions = [parsed]

        except Exception as e:
            print(f"Groq error: {e}")

    return {
        "success": True,
        "topic": request.topic,
        "recommended_hook_type": best_hook_type,
        "similar_patterns": relevant_hooks[:3],
        "generated_suggestions": suggestions
    }

@app.post("/reload")
async def reload_patterns():
    """Reload patterns from database"""
    await load_patterns_from_db()
    info = qdrant.get_collection(COLLECTION_NAME)
    return {"success": True, "patterns_count": info.points_count}

@app.get("/stats")
def get_stats():
    """Get statistics about learned patterns"""
    ensure_collection()

    # Get all patterns
    info = qdrant.get_collection(COLLECTION_NAME)

    # Scroll through all points to get hook type distribution
    results = qdrant.scroll(
        collection_name=COLLECTION_NAME,
        limit=100
    )

    hook_types = {}
    for point in results[0]:
        ht = point.payload.get("hook_type", "unknown")
        hook_types[ht] = hook_types.get(ht, 0) + 1

    return {
        "total_patterns": info.points_count,
        "hook_type_distribution": hook_types,
        "collection": COLLECTION_NAME
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Viral Pattern Learning API...")
    print("Endpoints:")
    print("  POST /learn - Add new pattern")
    print("  POST /search - Find similar patterns")
    print("  POST /suggest-hooks - Get AI-generated hook suggestions")
    print("  GET /stats - View statistics")
    uvicorn.run(app, host="127.0.0.1", port=8766)
