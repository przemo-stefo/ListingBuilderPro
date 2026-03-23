# backend/api/demo_wow_routes.py
# Purpose: WOW demo features — Competitor Inspire, Compliance Radar, EFSA Claims, Listing Guard
# NOT for: Core 5-step pipeline (that's in demo_routes.py)

import asyncio
import json
import re as _re

import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from database import get_db
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.demo_routes import MARKETPLACE_DOMAINS
from data.demo_samples import get_demo_competitor, get_demo_inspire_competitors
from data.efsa_claims import lookup_ingredients, auto_detect_ingredients
from services.groq_client import call_groq, sanitize_llm_input
from services.supplement_compliance import check_supplement_compliance
from services.ranking_juice_service import calculate_ranking_juice
from services.amazon_tos_checker import check_amazon_tos

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/demo", tags=["demo-wow"])


# --- Request Models ---

class CompetitorInspireRequest(BaseModel):
    """Input: competitor ASINs (scraped) OR pasted listings -> AI generates versions."""
    asins: List[str] = Field(default=[], max_length=5)
    # WHY: max 5 pasted competitors (same as ASINs) — prevents oversized prompts
    pasted_competitors: List[Dict[str, Any]] = Field(default=[], max_length=5)
    use_sample: bool = Field(default=False)
    marketplace: str = Field(default="DE", max_length=5)
    category: str = Field(default="")
    language: str = Field(default="de")
    # WHY: Keywords from DataDive/Helium10 CSV — LLM must use these in generated listings.
    # Max 100 keywords — _build_keywords_block() takes top 30 anyway.
    keywords: List[Dict[str, Any]] = Field(default=[], max_length=100)


class CompetitorScanRequest(BaseModel):
    asin: str = Field(default="B09COMPET1", min_length=10, max_length=10)
    marketplace: str = Field(default="DE", max_length=5)


class IngredientClaimsRequest(BaseModel):
    ingredients: List[str] = []
    current_bullets: List[str] = []
    title: str = ""


class ListingGuardRequest(BaseModel):
    original_title: str
    original_bullets: List[str] = []
    keywords: List[Dict[str, Any]] = []


# --- Competitor-Inspired Listing Generator ---

@router.post("/competitor-inspire")
@limiter.limit("3/minute")
async def demo_competitor_inspire(
    request: Request,
    req: CompetitorInspireRequest,
    db: Session = Depends(get_db),
):
    """Scrape competitor ASINs -> AI analyzes -> generates optimized listing versions."""
    competitors = []
    failed = []

    # WHY: 3 input modes — sample (demo), pasted (manual), or scraped (live)
    if req.use_sample:
        competitors = get_demo_inspire_competitors()
    elif req.pasted_competitors:
        # WHY: sanitize_llm_input strips injection patterns from user-pasted competitor data
        competitors = [
            {"asin": c.get("asin", "MANUAL"),
             "title": sanitize_llm_input(c.get("title", "")),
             "bullets": [sanitize_llm_input(b) for b in c.get("bullets", [])[:5]],
             "description": sanitize_llm_input(c.get("description", ""))}
            for c in req.pasted_competitors[:5] if c.get("title")
        ]
    elif req.asins:
        from services.scraper.amazon_scraper import AmazonListing, fetch_listing
        domain = MARKETPLACE_DOMAINS.get(req.marketplace.upper(), "amazon.de")

        async def _scrape_one(asin: str) -> dict:
            listing = AmazonListing(asin=asin.upper().strip(), marketplace=req.marketplace, domain=domain)
            listing = await fetch_listing(listing)
            return {"asin": listing.asin, "title": listing.title,
                    "bullets": listing.bullets, "description": listing.description,
                    "error": listing.error}

        scraped = await asyncio.gather(*[_scrape_one(a) for a in req.asins[:5]])
        competitors = [s for s in scraped if s["title"] and not s["error"]]
        failed = [s for s in scraped if s["error"]]

    if not competitors:
        return {"error": "Brak danych konkurentów — użyj próbki demo lub wklej ręcznie", "failed": failed}

    # WHY: RAG search runs async while we build the competitor block (saves 1-3s latency)
    from services.knowledge_service import search_knowledge

    async def _get_expert_context() -> str:
        try:
            return await search_knowledge(
                db, "Amazon listing optimization title structure bullet points keyword placement best practices",
                prompt_type="title", max_chunks=3,
            )
        except Exception as e:
            logger.warning("competitor_inspire_rag_error", error=str(e)[:80])
            return ""

    rag_task = asyncio.create_task(_get_expert_context())

    # WHY: Build competitor analysis block (runs while RAG search is in-flight)
    comp_block = _build_competitor_block(competitors)
    expert_context = await rag_task

    keywords_block = _build_keywords_block(req.keywords)
    expert_block = f"\n\nEXPERT KNOWLEDGE (Amazon listing best practices from real experts):\n{expert_context[:1500]}" if expert_context else ""

    lang_name = {"de": "German", "en": "English", "pl": "Polish", "fr": "French", "it": "Italian", "es": "Spanish"}.get(req.language, "German")
    category_hint = f"\nProduct category: {req.category}" if req.category else ""

    prompt = _build_inspire_prompt(len(competitors), category_hint, comp_block, keywords_block, expert_block, lang_name)

    # WHY: Reuse groq_client.call_groq() — shared key rotation + client caching (DRY)
    raw_response = ""
    try:
        raw_response, _usage = await asyncio.to_thread(call_groq, prompt, 0.7, 3000)
        result = _parse_llm_json(raw_response)
    except json.JSONDecodeError:
        logger.error("competitor_inspire_json_fail", raw=raw_response[:200])
        return {"error": "AI wygenerowało nieprawidłową odpowiedź — spróbuj ponownie", "competitors": competitors}
    except Exception as e:
        logger.error("competitor_inspire_llm_error", error=str(e)[:100])
        return {"error": f"Błąd generowania: {str(e)[:100]}", "competitors": competitors}

    logger.info("demo_competitor_inspire", competitors=len(competitors), failed=len(failed),
                versions=len(result.get("versions", [])))

    return {
        "competitors": competitors,
        "failed": failed,
        "common_keywords": result.get("common_keywords", []),
        "versions": result.get("versions", []),
    }


# --- WOW Feature 1: Competitor Compliance Radar ---

@router.post("/scan-competitor")
@limiter.limit("3/minute")
async def demo_scan_competitor(request: Request, req: CompetitorScanRequest):
    """Scan competitor ASIN for TOS + EU compliance violations."""
    competitor = get_demo_competitor()
    competitor_marketplace = f"amazon_{req.marketplace.lower()}"

    tos_scan = check_amazon_tos(
        title=competitor["title"], bullets=competitor.get("bullets", []),
        description=competitor.get("description", ""), backend_keywords="",
        marketplace=competitor_marketplace,
    )
    compliance = check_supplement_compliance(
        title=competitor["title"], bullets=competitor.get("bullets", []),
        description=competitor.get("description", ""),
        manufacturer=competitor.get("manufacturer", ""),
        category=competitor.get("category", ""),
    )

    total_issues = tos_scan["violation_count"] + compliance["summary"]["fail_count"]
    suppression_risk = tos_scan.get("suppression_risk", False)

    if suppression_risk or total_issues >= 5:
        risk_level, risk_message = "HIGH", "Suppression within 30 days — high probability of listing removal"
    elif total_issues >= 3:
        risk_level, risk_message = "MEDIUM", "Review flag likely within 60 days — ranking penalties expected"
    else:
        risk_level, risk_message = "LOW", "Minor issues — may receive warnings but low removal risk"

    logger.info("demo_scan_competitor", tos_count=tos_scan["violation_count"],
                compliance_score=compliance["score"], risk=risk_level)

    return {
        "competitor": {
            "title": competitor["title"], "brand": competitor["brand"],
            "asin": competitor["asin"], "bullets": competitor["bullets"][:3],
        },
        "tos_scan": tos_scan,
        "compliance": compliance,
        "risk_summary": {
            "level": risk_level, "message": risk_message,
            "total_issues": total_issues,
            "tos_violations": tos_scan["violation_count"],
            "compliance_fails": compliance["summary"]["fail_count"],
            "compliance_warnings": compliance["summary"]["warning_count"],
            "suppression_risk": suppression_risk,
        },
    }


# --- WOW Feature 2: EFSA Ingredient-to-Claims Mapper ---

@router.post("/ingredient-claims")
@limiter.limit("5/minute")
async def demo_ingredient_claims(request: Request, req: IngredientClaimsRequest):
    """Map supplement ingredients to EFSA-approved EU health claims."""
    ingredients = req.ingredients
    if not ingredients and (req.title or req.current_bullets):
        ingredients = auto_detect_ingredients(req.title, req.current_bullets)

    if not ingredients:
        return {"ingredients": [], "auto_detected": False, "error": "No ingredients provided or detected"}

    results = lookup_ingredients(ingredients, req.current_bullets)
    total_forbidden = sum(len(r["forbidden_in_listing"]) for r in results)
    total_approved = sum(len(r["approved_claims"].get("de", [])) for r in results if r["found"])

    logger.info("demo_ingredient_claims", count=len(ingredients),
                forbidden=total_forbidden, approved=total_approved)

    return {
        "ingredients": results,
        "auto_detected": not bool(req.ingredients),
        "summary": {
            "total_ingredients": len(results),
            "with_efsa_data": sum(1 for r in results if r["found"]),
            "forbidden_claims_found": total_forbidden,
            "approved_claims_available": total_approved,
        },
    }


# --- WOW Feature 3: Listing Change Guard (Simulation) ---

@router.post("/listing-guard")
@limiter.limit("5/minute")
async def demo_listing_guard(request: Request, req: ListingGuardRequest):
    """Simulate Amazon title/bullet changes and show keyword impact."""
    modified_title, changes = _simulate_amazon_changes(req.original_title)
    modified_bullets = _simulate_bullet_changes(req.original_bullets)

    kw_for_rj = [{"phrase": k.get("keyword", k.get("phrase", "")),
                   "search_volume": k.get("search_volume", 0)}
                  for k in req.keywords[:50]]

    before_rj = calculate_ranking_juice(
        keywords=kw_for_rj, title=req.original_title,
        bullets=req.original_bullets, backend="", description="",
    )
    after_rj = calculate_ranking_juice(
        keywords=kw_for_rj, title=modified_title,
        bullets=modified_bullets, backend="", description="",
    )

    original_text = f"{req.original_title} {' '.join(req.original_bullets)}".lower()
    modified_text = f"{modified_title} {' '.join(modified_bullets)}".lower()

    lost_keywords = []
    for kw in req.keywords[:20]:
        keyword = kw.get("keyword", kw.get("phrase", ""))
        if keyword.lower() in original_text and keyword.lower() not in modified_text:
            lost_keywords.append({
                "keyword": keyword,
                "search_volume": kw.get("search_volume", 0),
                "ranking_juice": kw.get("ranking_juice", 0),
            })

    rj_drop = round(before_rj["score"] - after_rj["score"], 1)
    logger.info("demo_listing_guard", changes=len(changes), lost_kw=len(lost_keywords), rj_drop=rj_drop)

    return {
        "original": {"title": req.original_title, "bullets": req.original_bullets},
        "amazon_modified": {"title": modified_title, "bullets": modified_bullets},
        "changes": changes,
        "rj_impact": {
            "before": before_rj["score"], "after": after_rj["score"], "drop": rj_drop,
            "before_grade": before_rj["grade"], "after_grade": after_rj["grade"],
        },
        "lost_keywords": lost_keywords,
        "alert": {
            "type": "TITLE_CHANGE", "detected_ago": "2 days ago",
            "severity": "HIGH" if rj_drop > 10 else ("MEDIUM" if rj_drop > 5 else "LOW"),
        },
    }


# --- Helpers ---

def _build_competitor_block(competitors: list) -> str:
    """Build competitor analysis block for LLM prompt."""
    comp_block = ""
    for i, c in enumerate(competitors, 1):
        bullets_text = "\n".join(f"  - {b}" for b in c["bullets"][:5])
        comp_block += f"""
COMPETITOR {i} (ASIN: {c['asin']}):
  Title: {c['title']}
  Bullets:
{bullets_text}
  Description: {c['description'][:300]}
"""
    return comp_block


def _build_keywords_block(keywords: list) -> str:
    """Build keywords block from DataDive/Helium10 upload for LLM prompt."""
    if not keywords:
        return ""
    sorted_kw = sorted(keywords, key=lambda k: k.get("ranking_juice", k.get("search_volume", 0)), reverse=True)
    top_kw = sorted_kw[:30]
    kw_lines = [f"  {k.get('keyword', k.get('phrase', ''))} (vol: {k.get('search_volume', 0)}, RJ: {k.get('ranking_juice', 0)})"
                 for k in top_kw if k.get("keyword") or k.get("phrase")]
    if not kw_lines:
        return ""
    return "\n\nRESEARCHED KEYWORDS (from DataDive/Helium10 — MUST use top keywords in listings):\n" + "\n".join(kw_lines)


def _build_inspire_prompt(
    n_competitors: int, category_hint: str, comp_block: str,
    keywords_block: str, expert_block: str, lang_name: str,
) -> str:
    """Build the full LLM prompt for competitor-inspired listing generation."""
    return f"""You are an expert Amazon listing copywriter. Analyze these {n_competitors} competitor listings and create optimized listing versions.
{category_hint}
{comp_block}{keywords_block}{expert_block}

TASK:
1. First, identify the TOP 15 keywords — combine competitor analysis WITH the researched keywords above (if provided). Prioritize keywords with highest search volume and Ranking Juice.
2. Then create exactly 3 listing versions in {lang_name}:

VERSION A — "SEO Aggressive": Maximum keyword density, every high-volume keyword in title+bullets. Focus: ranking.
VERSION B — "Conversion Focused": Benefit-driven copy, emotional triggers, clear USPs. Focus: click-through + conversion.
VERSION C — "Balanced": Best of both — strong keywords + compelling copy.

AMAZON LISTING STRUCTURE RULES:
- Title: Brand + main keyword + key attributes (size, count, form). Max 200 chars. Front-load highest-volume keywords.
- Bullets: Start each with CAPS keyword phrase. One benefit per bullet. Include search terms naturally. Max 200 chars each.
- Description: Expand on benefits, use cases, trust signals. HTML allowed: <b>, <br>, <ul>, <li>. Max 1000 chars.
- Backend keywords: Space-separated, no commas, NO duplicates from title/bullets. Max 250 chars. Use synonyms and long-tail variations.
- NEVER use superlatives (best, #1, top) — Amazon TOS violation.
- NEVER use health claims without certification — EU compliance risk.

For each version output:
- title (max 200 chars)
- bullets (array of exactly 5 strings, max 200 chars each)
- description (max 1000 chars)
- backend_keywords (max 250 chars, space-separated)

Output as valid JSON:
{{
  "common_keywords": ["kw1", "kw2", ...],
  "versions": [
    {{
      "name": "SEO Aggressive",
      "title": "...",
      "bullets": ["...", "...", "...", "...", "..."],
      "description": "...",
      "backend_keywords": "..."
    }},
    ...
  ]
}}

RULES:
- Write in {lang_name} ONLY
- Never copy competitor titles verbatim — inspire, don't plagiarize
- Each version must be meaningfully different in approach
- Include specific numbers, certifications, and USPs where visible in competitor data
- If researched keywords provided — they MUST appear in the listings (especially top 10 by volume)
- Output ONLY valid JSON, no markdown, no explanation"""


def _parse_llm_json(raw: str) -> dict:
    """Parse LLM JSON response, handling markdown wrappers and type mismatches."""
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)

    # WHY: LLM sometimes returns common_keywords as string instead of array
    kw = result.get("common_keywords", [])
    if isinstance(kw, str):
        result["common_keywords"] = [k.strip() for k in kw.split(",") if k.strip()]

    # WHY: Sanitize versions — LLM can return bullets as string, wrong count, etc.
    for v in result.get("versions", []):
        if isinstance(v.get("bullets"), str):
            v["bullets"] = [b.strip() for b in v["bullets"].split("\n") if b.strip()]
        if not isinstance(v.get("bullets"), list):
            v["bullets"] = []
        while len(v["bullets"]) < 5:
            v["bullets"].append("")
        v["bullets"] = v["bullets"][:5]

    return result


def _simulate_amazon_changes(title: str) -> tuple:
    """Simulate how Amazon silently modifies listing titles."""
    changes = []
    modified = title

    if " - " in modified:
        dash_count = modified.count(" - ")
        modified = modified.replace(" - ", " ")
        changes.append({"type": "SEPARATOR_REMOVAL",
                        "description": f"{dash_count} dash separators removed (reduces exact-match indexing)",
                        "impact": "MEDIUM"})

    if len(modified) > 60:
        cut_point = modified[:60].rfind(" ")
        if cut_point > 30:
            original_len = len(modified)
            modified = modified[:cut_point]
            changes.append({"type": "TRUNCATION",
                            "description": f"Title truncated from {original_len} to {len(modified)} chars (mobile display limit)",
                            "impact": "HIGH"})

    promo_patterns = [
        (r'\s*(?:Premium|Hochdosiert|Best\s*(?:Price|Quality)|Top\s*Quality)\b', ''),
        (r'\s*(?:guaranteed|garantiert)\s*', ' '),
        (r'!!!+', ''),
        (r'\s*#1\s*', ' '),
    ]
    for pattern, replacement in promo_patterns:
        new_modified = _re.sub(pattern, replacement, modified, flags=_re.IGNORECASE)
        if new_modified != modified:
            changes.append({"type": "PROMO_REMOVAL",
                            "description": "Promotional/superlative content removed by Amazon",
                            "impact": "MEDIUM"})
            modified = new_modified

    words = modified.split()
    if len(words) > 1:
        first_word = words[0]
        common_starts = {"vitamin", "spirulina", "omega", "100%", "natürliche", "der", "die", "das"}
        if first_word.lower() not in common_starts and first_word[0].isupper():
            modified = " ".join(words[1:])
            changes.append({"type": "BRAND_REMOVAL",
                            "description": f"Brand '{first_word}' removed from title start",
                            "impact": "LOW"})

    modified = _re.sub(r'\s+', ' ', modified).strip()
    return modified, changes


def _simulate_bullet_changes(bullets: List[str]) -> List[str]:
    """Simulate Amazon bullet point modifications."""
    if not bullets:
        return []
    modified = []
    for bullet in bullets:
        b = bullet
        if len(b) > 200:
            cut = b[:200].rfind(" ")
            if cut > 100:
                b = b[:cut] + "..."
        b = _re.sub(r'^([A-ZÄÖÜ\s]{10,}):', lambda m: m.group(0).title(), b)
        modified.append(b)
    return modified
