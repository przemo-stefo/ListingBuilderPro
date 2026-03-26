# backend/services/ad_copy_service.py
# Purpose: Generate Meta ad copy, headlines, video hooks, creative briefs using RAG
# NOT for: Listing optimization (optimizer_service.py) or general Q&A (qa_service.py)

from __future__ import annotations

import asyncio
import json
from typing import Dict
from groq import Groq
from sqlalchemy.orm import Session
from config import settings
from services.knowledge_service import _get_search_rows, _expand_query, _get_embedding_if_needed, _format_chunks_with_sources
import structlog

logger = structlog.get_logger()

MODEL = "llama-3.3-70b-versatile"

# WHY: These categories match Barry Hott, Ecom Talent, Fraser Cottrell, Katie Floyd, and copywriting courses
AD_CATEGORIES = ["ad_creative", "creative_strategy", "copywriting", "marketing_psychology"]

LANG_RULE = (
    "Answer in the SAME LANGUAGE as the product title and features above. "
    "If they are in Polish, write ads in Polish. If in English, write in English."
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _product_block(title: str, features: list[str], audience: str) -> str:
    """Reusable product info block for all prompts."""
    features_block = "\n".join(f"- {f}" for f in features)
    audience_block = f"\nTARGET AUDIENCE: {audience}\n" if audience else ""
    return f"PRODUCT: {title}\nFEATURES:\n{features_block}\n{audience_block}"


def _groq_call(prompt: str, max_tokens: int = 1200, temperature: float = 0.7) -> str:
    """Call Groq LLM with API key rotation on 429."""
    keys = settings.groq_api_keys
    last_error = None
    for i, key in enumerate(keys):
        try:
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = e
            if "429" in str(e) or "rate_limit" in str(e):
                logger.warning("groq_rate_limit", key_index=i)
                continue
            raise
    raise last_error  # type: ignore[misc]


def _parse_json(raw: str) -> list | dict:
    """Strip markdown fences + parse JSON from LLM response."""
    clean = raw.strip("`").removeprefix("json").strip()
    return json.loads(clean)


async def _search_ad_knowledge(
    db: Session, query: str
) -> tuple[str, list[str]]:
    """Search knowledge base with ad-specific categories.

    WHY: We target ad_creative/creative_strategy/copywriting/marketing_psychology
    specifically — these contain Barry Hott, Ecom Talent, Cottrell, and Katie Floyd courses.
    Falls back to all categories if no results found.
    """
    search_query = await _expand_query(query)
    query_embedding = await _get_embedding_if_needed(search_query)

    rows = await _get_search_rows(db, search_query, AD_CATEGORIES, 8, query_embedding)

    # WHY: Fallback to broader search if ad-specific categories return nothing
    if not rows:
        rows = await _get_search_rows(db, search_query, None, 8, query_embedding)

    if not rows:
        return "", []

    return _format_chunks_with_sources(rows)


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_ad_prompt(
    product_title: str,
    product_features: list[str],
    target_audience: str,
    context: str,
    platform: str,
    framework: str = "mixed",
) -> str:
    """Build ad copy prompt — supports mixed, aida, pas frameworks."""
    product = _product_block(product_title, product_features, target_audience)

    if framework == "aida":
        variations = """Generate exactly 3 ad variations using the AIDA framework:
1. "aida_curiosity" — Attention via curiosity gap, Interest through benefits, Desire with social proof, Action with urgency
2. "aida_pain" — Attention via pain point, Interest through empathy, Desire with transformation, Action with scarcity
3. "aida_social" — Attention via social proof, Interest through FOMO, Desire with exclusivity, Action with community"""
        types = '"aida_curiosity", "aida_pain", "aida_social"'
    elif framework == "pas":
        variations = """Generate exactly 3 ad variations using the PAS framework:
1. "pas_emotional" — Problem stated emotionally, Agitate with consequences, Solve with product benefits
2. "pas_logical" — Problem stated with data/facts, Agitate with missed opportunity, Solve with ROI/results
3. "pas_story" — Problem told as a story, Agitate with relatable struggle, Solve with transformation"""
        types = '"pas_emotional", "pas_logical", "pas_story"'
    else:
        variations = """Generate exactly 4 ad variations. Each uses a different proven approach:
1. "hook" — Pattern interrupt / curiosity hook (Barry Hott style). Stop the scroll with a bold, unexpected opening.
2. "story" — Story-based / founder narrative (Fraser Cottrell style). Tell a compelling origin or transformation story.
3. "benefit" — Direct benefit / social proof (Ecom Talent style). Lead with measurable results and testimonials.
4. "relatable" — Relatable + Result (Katie Floyd style). Use the 7-step formula: Pain Confession, Turning Point, Old vs New, Specific How, Proof, Invitation, CTA."""
        types = '"hook", "story", "benefit", "relatable"'

    return f"""You are an expert {platform} ad copywriter trained on courses from Barry Hott, Ecom Talent, Fraser Cottrell, and Katie Floyd. Generate ad copy using the expert knowledge below.

EXPERT KNOWLEDGE (from ad creative courses):
{context}

{product}
PLATFORM: {platform}

{variations}

Each variation MUST contain:
- "type": one of {types}
- "headline": short attention-grabbing headline, max 40 characters
- "primary_text": the MAIN ad body text, 2-4 compelling sentences, 150-300 characters. Include product benefits, pain points, or a story. This is the most important part of the ad.
- "description": a persuasive call-to-action or key benefit summary, 40-80 characters. NEVER just one word — write a complete phrase.

{LANG_RULE}

Return ONLY valid JSON array, no markdown, no explanation:
[{{"type":"...","headline":"...","primary_text":"...","description":"..."}}, ...]"""


def _build_headlines_prompt(
    product_title: str,
    product_features: list[str],
    target_audience: str,
    context: str,
) -> str:
    """Build headline generation prompt — Bly/Schwartz/Whitman formulas."""
    product = _product_block(product_title, product_features, target_audience)

    return f"""You are an expert headline copywriter trained on Robert Bly, Eugene Schwartz, Drew Eric Whitman, and modern Meta ad formulas. Generate headlines using the expert knowledge below.

EXPERT KNOWLEDGE:
{context}

{product}

Generate exactly 10 headlines in JSON format. Use diverse formulas:
- How-to, Number list, Question, Command, Testimonial
- Curiosity gap, Fear of missing out, Newsjacking, Before/After, Contrarian

Each headline targets a different awareness stage (unaware, problem_aware, solution_aware, product_aware, most_aware).

{LANG_RULE}

Return ONLY valid JSON array:
[{{"headline":"...","formula":"How-to","awareness_stage":"problem_aware"}}, ...]"""


def _build_hooks_prompt(
    product_title: str,
    product_features: list[str],
    target_audience: str,
    context: str,
) -> str:
    """Build video hook prompt — Michael Diaz 3-element formula (visual + caption + verbal)."""
    product = _product_block(product_title, product_features, target_audience)

    return f"""You are an expert video ad creative strategist trained on Michael Diaz's 3-element hook formula and modern Meta ad creative courses.

EXPERT KNOWLEDGE:
{context}

{product}

Generate exactly 5 scroll-stopping video hooks. Each hook has 3 simultaneous elements:
1. VISUAL — What the viewer SEES in the first 2 seconds
2. CAPTION — Bold text overlay on screen (max 8 words)
3. VERBAL — What the talent/voiceover SAYS (1-2 sentences max)

Use different angles:
- Hook 1: Pattern interrupt (something unexpected)
- Hook 2: Before/after transformation
- Hook 3: Social proof / testimonial style
- Hook 4: Problem agitation
- Hook 5: Curiosity approach

{LANG_RULE}

Return ONLY valid JSON array:
[{{"angle":"Pattern interrupt","visual":"...","caption":"...","verbal":"...","why_it_works":"..."}}, ...]"""


def _build_brief_prompt(
    product_title: str,
    product_features: list[str],
    target_audience: str,
    context: str,
) -> str:
    """Build 11-step creative brief prompt."""
    product = _product_block(product_title, product_features, target_audience)

    return f"""You are a senior creative strategist at a performance marketing agency. Create a comprehensive creative brief using expert knowledge from ad creative courses.

EXPERT KNOWLEDGE:
{context}

{product}

Create an 11-step creative brief:
1. ICP — Who exactly is this for? Demographics, psychographics, daily habits.
2. Pain Points — Top 3-5 specific pains this product solves.
3. Desires — Top 3-5 desired outcomes the customer fantasizes about.
4. Hesitations — Top 3-5 objections/fears that stop them from buying.
5. Unique Mechanism — What makes this product different?
6. Proof Elements — Types of proof available.
7. Creative Angles — 3 distinct angles to approach the ad from.
8. Recommended Formats — For each angle, suggest 2-3 ad formats.
9. Copy Hooks — For each angle, write 3 scroll-stopping opening lines.
10. CTA Strategy — What action to drive and how to reduce friction.
11. Testing Plan — Priority order for testing creative variations.

{LANG_RULE}

Return ONLY valid JSON object:
{{"icp":"...","pain_points":["..."],"desires":["..."],"hesitations":["..."],"unique_mechanism":"...","proof_elements":["..."],"creative_angles":[{{"angle":"...","description":"..."}}],"recommended_formats":[{{"angle":"...","formats":["..."]}}],"copy_hooks":[{{"angle":"...","hooks":["..."]}}],"cta_strategy":"...","testing_plan":"..."}}"""


# ---------------------------------------------------------------------------
# Public generation functions
# ---------------------------------------------------------------------------

async def generate_ad_copy(
    product_title: str,
    product_features: list[str],
    target_audience: str,
    db: Session,
    platform: str = "facebook",
    framework: str = "mixed",
) -> Dict:
    """Generate ad copy variations using Groq LLM with RAG context."""
    search_query = f"{product_title} {' '.join(product_features[:3])}"
    context, source_names = await _search_ad_knowledge(db, search_query)

    logger.info("ad_copy_generate", product=product_title[:60], platform=platform, framework=framework, sources=len(source_names))

    prompt = _build_ad_prompt(product_title, product_features, target_audience, context, platform, framework)
    raw = await asyncio.to_thread(_groq_call, prompt)

    try:
        variations = _parse_json(raw)
    except json.JSONDecodeError:
        logger.error("ad_copy_json_parse_failed", raw=raw[:200])
        variations = [{"type": "error", "headline": "Generation failed", "primary_text": raw[:125], "description": "Retry"}]

    return {"variations": variations, "sources_used": len(source_names), "sources": source_names[:10], "platform": platform}


async def generate_headlines(
    product_title: str,
    product_features: list[str],
    target_audience: str,
    db: Session,
) -> Dict:
    """Generate 10 headlines using diverse copywriting formulas."""
    search_query = f"headline formulas {product_title}"
    context, source_names = await _search_ad_knowledge(db, search_query)

    logger.info("headlines_generate", product=product_title[:60], sources=len(source_names))

    prompt = _build_headlines_prompt(product_title, product_features, target_audience, context)
    raw = await asyncio.to_thread(_groq_call, prompt, max_tokens=1500)

    try:
        headlines = _parse_json(raw)
    except json.JSONDecodeError:
        logger.error("headlines_json_parse_failed", raw=raw[:200])
        headlines = [{"headline": "Generation failed", "formula": "error", "awareness_stage": "unaware"}]

    return {"headlines": headlines, "sources_used": len(source_names), "sources": source_names[:10]}


async def generate_hooks(
    product_title: str,
    product_features: list[str],
    target_audience: str,
    db: Session,
) -> Dict:
    """Generate 5 video hooks using Michael Diaz's 3-element formula."""
    search_query = f"video hook formula {product_title}"
    context, source_names = await _search_ad_knowledge(db, search_query)

    logger.info("hooks_generate", product=product_title[:60], sources=len(source_names))

    prompt = _build_hooks_prompt(product_title, product_features, target_audience, context)
    raw = await asyncio.to_thread(_groq_call, prompt, max_tokens=1500)

    try:
        hooks = _parse_json(raw)
    except json.JSONDecodeError:
        logger.error("hooks_json_parse_failed", raw=raw[:200])
        hooks = [{"angle": "error", "visual": "N/A", "caption": "Failed", "verbal": raw[:100], "why_it_works": "N/A"}]

    return {"hooks": hooks, "sources_used": len(source_names), "sources": source_names[:10]}


async def generate_brief(
    product_title: str,
    product_features: list[str],
    target_audience: str,
    db: Session,
) -> Dict:
    """Generate an 11-step creative brief."""
    search_query = f"creative brief strategy {product_title}"
    context, source_names = await _search_ad_knowledge(db, search_query)

    logger.info("brief_generate", product=product_title[:60], sources=len(source_names))

    prompt = _build_brief_prompt(product_title, product_features, target_audience, context)
    # WHY: Brief is the longest output — higher token limit + lower temp for consistency
    raw = await asyncio.to_thread(_groq_call, prompt, max_tokens=2500, temperature=0.5)

    try:
        brief = _parse_json(raw)
    except json.JSONDecodeError:
        logger.error("brief_json_parse_failed", raw=raw[:200])
        brief = {"icp": "Generation failed", "pain_points": [], "desires": [], "hesitations": [],
                 "unique_mechanism": "N/A", "proof_elements": [], "creative_angles": [],
                 "recommended_formats": [], "copy_hooks": [], "cta_strategy": "N/A", "testing_plan": "N/A"}

    return {"brief": brief, "sources_used": len(source_names), "sources": source_names[:10]}
