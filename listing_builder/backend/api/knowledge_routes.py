# backend/api/knowledge_routes.py
# Purpose: Knowledge base endpoints — search, stats, and Expert Q&A chat
# NOT for: Listing optimization (that's optimizer_service + optimizer_routes)

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_db
from services.knowledge_service import search_knowledge
from services.qa_service import ask_expert

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/search")
@limiter.limit("20/minute")
async def knowledge_search(
    request: Request,
    q: str = Query(..., min_length=2, max_length=200),
    prompt_type: str = Query("title", pattern="^(title|bullets|description)$"),
    max_chunks: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Search knowledge base — debug endpoint for testing retrieval quality."""
    context = search_knowledge(db, q, prompt_type, max_chunks)
    return {
        "query": q,
        "prompt_type": prompt_type,
        "context_length": len(context),
        "context": context,
    }


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)


class ChatResponse(BaseModel):
    answer: str
    sources_used: int
    has_context: bool


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def expert_chat(
    request: Request,
    body: ChatRequest,
    db: Session = Depends(get_db),
):
    """Expert Q&A — ask Amazon questions, answered using Inner Circle transcript RAG."""
    result = await ask_expert(body.question, db)
    return result


@router.get("/stats")
async def knowledge_stats(db: Session = Depends(get_db)):
    """Chunk and file counts per category."""
    rows = db.execute(text(
        "SELECT category, COUNT(*) as chunks, COUNT(DISTINCT filename) as files "
        "FROM knowledge_chunks GROUP BY category ORDER BY chunks DESC"
    )).fetchall()

    total_chunks = sum(r[1] for r in rows)
    total_files = db.execute(text(
        "SELECT COUNT(DISTINCT filename) FROM knowledge_chunks"
    )).scalar()

    return {
        "total_chunks": total_chunks,
        "total_files": total_files,
        "categories": [
            {"category": r[0], "chunks": r[1], "files": r[2]}
            for r in rows
        ],
    }
