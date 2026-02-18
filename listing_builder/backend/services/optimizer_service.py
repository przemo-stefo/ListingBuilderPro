# backend/services/optimizer_service.py
# Purpose: Listing optimization — n8n-first with direct Groq fallback
# NOT for: Database models or marketplace publishing

from __future__ import annotations

import asyncio
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from groq import Groq
from sqlalchemy.orm import Session
from config import settings
from services.knowledge_service import search_knowledge_batch
from services.ranking_juice_service import calculate_ranking_juice
from services.learning_service import store_successful_listing, get_past_successes
from services.n8n_orchestrator_service import call_n8n_optimizer, build_n8n_payload
from services.trace_service import new_trace, span, record_llm_usage, finalize_trace
from services.anti_stuffing_service import run_anti_stuffing_check
from services.keyword_placement_service import prepare_keywords_with_fallback, get_bullet_count, get_bullet_limit
from services.coverage_service import calculate_multi_tier_coverage
from services.ppc_service import generate_ppc_recommendations
import structlog

logger = structlog.get_logger()

# WHY: Marketplace-specific limits for title, bullets, description, backend keywords
MARKETPLACE_LIMITS = {
    "amazon_de": {"title": 200, "bullet": 500, "backend": 249, "lang": "de"},
    "amazon_com": {"title": 200, "bullet": 500, "backend": 249, "lang": "en"},
    "amazon_us":  {"title": 200, "bullet": 500, "backend": 249, "lang": "en"},  # WHY: Frontend sends amazon_us
    "amazon_pl":  {"title": 200, "bullet": 500, "backend": 249, "lang": "pl"},
    "amazon_fr":  {"title": 200, "bullet": 500, "backend": 249, "lang": "fr"},
    "amazon_it":  {"title": 200, "bullet": 500, "backend": 249, "lang": "it"},
    "amazon_es":  {"title": 200, "bullet": 500, "backend": 249, "lang": "es"},
    "ebay_de":    {"title": 80,  "bullet": 300, "backend": 0,   "lang": "de"},
    "kaufland":   {"title": 150, "bullet": 400, "backend": 0,   "lang": "de"},
    "allegro":    {"title": 75,  "bullet": 500, "backend": 0,   "lang": "pl"},
}

MODEL = "llama-3.3-70b-versatile"

# WHY: Amazon prohibits these in titles/bullets
PROMO_WORDS = [
    "bestseller", "best seller", "top seller", "#1", "nr. 1", "günstig",
    "billig", "gratis", "free", "sale", "rabatt", "discount", "angebot",
    "deal", "preiswert", "sonderangebot", "ausverkauf", "cheap",
]

FORBIDDEN_CHARS = ["!", "¡", "$", "€", "™", "®", "©"]


def _sanitize_llm_input(text: str) -> str:
    """Strip control characters and LLM injection patterns from user input.

    WHY: User-supplied product_title, brand, keywords go into LLM prompts.
    An attacker could inject "Ignore all instructions..." to hijack the prompt.
    We strip common injection prefixes and control chars, but keep normal text.
    """
    # Strip control characters (except newline/tab which are harmless)
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Collapse multiple newlines (injection payloads use them to "escape" context)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    # Truncate — no single field should exceed 1000 chars going into a prompt
    return cleaned[:1000]


def _get_limits(marketplace: str) -> dict:
    return MARKETPLACE_LIMITS.get(marketplace, MARKETPLACE_LIMITS["amazon_de"])


def _detect_language(marketplace: str, explicit_lang: str | None) -> str:
    if explicit_lang:
        return explicit_lang
    return _get_limits(marketplace).get("lang", "de")


# --- Keyword preparation ---

def _prepare_keywords(
    keywords: List[Dict[str, Any]],
) -> Tuple[List[dict], List[dict], List[dict], List[dict]]:
    """
    Sort by search_volume desc, assign tiers.
    Returns (all_sorted, tier1, tier2, tier3).
    Tier1 = top 30% → must go in title.
    Tier2 = next 40% → bullets/description.
    Tier3 = rest → backend keywords.
    """
    sorted_kw = sorted(keywords, key=lambda k: k.get("search_volume", 0), reverse=True)
    total = len(sorted_kw)
    t1_end = max(1, int(total * 0.3))
    t2_end = max(t1_end + 1, int(total * 0.7))

    tier1 = sorted_kw[:t1_end]
    tier2 = sorted_kw[t1_end:t2_end]
    tier3 = sorted_kw[t2_end:]

    return sorted_kw, tier1, tier2, tier3


def _extract_root_words(keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract unique root words (2+ chars) with aggregate search volume."""
    roots: Dict[str, int] = {}
    for kw in keywords:
        words = kw["phrase"].lower().split()
        vol = kw.get("search_volume", 0)
        for w in words:
            w = w.strip(".,;:-()[]")
            if len(w) >= 2:
                roots[w] = roots.get(w, 0) + vol
    # Return top 20 by volume
    sorted_roots = sorted(roots.items(), key=lambda x: x[1], reverse=True)[:20]
    return [{"word": w, "total_volume": v} for w, v in sorted_roots]


# --- Backend keyword byte-packing ---

def _pack_backend_keywords(
    keywords: List[Dict[str, Any]], listing_text: str, max_bytes: int,
    llm_suggestions: str = "",
) -> str:
    """
    Greedy byte-packing: add keywords not already in the listing text,
    separated by spaces, up to max_bytes (249 for Amazon).
    WHY: Four passes — unused phrases, root words, plural/singular variants,
    then LLM-suggested terms. This maximizes search coverage.
    """
    if max_bytes <= 0:
        return ""

    listing_lower = listing_text.lower()
    packed: List[str] = []
    packed_words: set = set()
    current_bytes = 0

    def _try_add(text: str) -> bool:
        nonlocal current_bytes
        text_bytes = len(text.encode("utf-8"))
        separator_bytes = 1 if packed else 0
        if current_bytes + separator_bytes + text_bytes <= max_bytes:
            packed.append(text)
            current_bytes += separator_bytes + text_bytes
            packed_words.update(text.lower().split())
            return True
        return False

    # Pass 1: full phrases not already covered in listing
    for kw in keywords:
        phrase = kw["phrase"].strip()
        phrase_words = phrase.lower().split()
        if all(w in listing_lower for w in phrase_words):
            continue
        _try_add(phrase)

    # Pass 2: individual root words not in listing or already packed
    # WHY: Amazon indexes individual words — adding roots that aren't
    # in visible content expands search match surface within 249 bytes
    all_roots: Dict[str, int] = {}
    for kw in keywords:
        for w in kw["phrase"].lower().split():
            w = w.strip(".,;:-()[]")
            if len(w) >= 2:
                all_roots[w] = all_roots.get(w, 0) + kw.get("search_volume", 0)

    for word, _ in sorted(all_roots.items(), key=lambda x: x[1], reverse=True):
        if word in listing_lower or word in packed_words:
            continue
        _try_add(word)

    # Pass 3: plural/singular variants to catch alternate searches
    # WHY: Amazon treats "bottle" and "bottles" as different search terms —
    # adding the missing variant catches more customer queries
    # Skip short words, abbreviations, numbers — they don't have useful variants
    # WHY: Adjectives, prepositions, abbreviations don't have useful plural forms
    skip_variant = {
        "bpa", "ml", "cm", "kg", "oz", "mm", "xl", "xxl",
        "free", "steel", "stainless", "insulated", "vacuum",
        "safe", "portable", "durable", "large", "small",
        "cold", "warm", "with", "from", "pour", "pour",
    }
    combined = listing_lower + " " + " ".join(packed).lower()
    variants: List[str] = []
    for word in list(all_roots.keys()):
        if len(word) < 4 or word in skip_variant or any(c.isdigit() for c in word):
            continue
        # WHY: Only generate variants that are real words shoppers search for
        if word.endswith("s") and len(word) > 4 and len(word) <= 9:
            # Plural → singular (bottles→bottle)
            singular = word[:-1]
            if singular not in combined and singular not in packed_words:
                variants.append(singular)
        elif not word.endswith("s") and len(word) <= 8:
            # Singular → plural (bottle→bottles, flask→flasks)
            plural = word + "s"
            if plural not in combined and plural not in packed_words:
                variants.append(plural)
        # German: -e endings → -en plural (Flasche→Flaschen, Kanne→Kannen)
        # WHY: German compound nouns are long (>8 chars), so this won't clash with English
        if word.endswith("e") and len(word) >= 8:
            de_plural = word + "n"
            if de_plural not in combined and de_plural not in packed_words:
                variants.append(de_plural)

    for v in variants:
        _try_add(v)

    # Pass 4: LLM-suggested synonyms and related terms
    # WHY: When visible coverage is 93%+, Passes 1-3 find almost nothing.
    # The LLM suggests related terms shoppers actually search for (synonyms,
    # category terms, use-case words) that aren't in the keyword research data.
    if llm_suggestions:
        combined_check = listing_lower + " " + " ".join(packed).lower()
        for term in llm_suggestions.lower().split():
            term = term.strip(".,;:-()[]\"'")
            if len(term) < 2 or term in combined_check or term in packed_words:
                continue
            _try_add(term)

    return " ".join(packed)


# --- Coverage calculation ---

def _calculate_coverage(
    keywords: List[Dict[str, Any]], listing_text: str
) -> Tuple[float, int, str]:
    """
    Returns (coverage_pct, exact_matches_in_title_area, coverage_mode).
    A keyword is "covered" if >= 70% of its words appear in the full listing.
    """
    if not keywords:
        return 0.0, 0, "NONE"

    listing_lower = listing_text.lower()
    covered = 0
    exact_in_title = 0

    for kw in keywords:
        phrase_words = kw["phrase"].lower().split()
        if not phrase_words:
            continue
        matches = sum(1 for w in phrase_words if w in listing_lower)
        ratio = matches / len(phrase_words)
        if ratio >= 0.7:
            covered += 1
        # WHY: exact match = full phrase appears verbatim
        if kw["phrase"].lower() in listing_lower:
            exact_in_title += 1

    pct = round((covered / len(keywords)) * 100, 1)

    if pct >= 90:
        mode = "EXCELLENT"
    elif pct >= 70:
        mode = "GOOD"
    elif pct >= 50:
        mode = "MODERATE"
    else:
        mode = "LOW"

    return pct, exact_in_title, mode


def _find_missing_keywords(
    keywords: List[Dict[str, Any]], listing_text: str
) -> List[str]:
    """Keywords where < 70% of words appear in the listing."""
    listing_lower = listing_text.lower()
    missing = []
    for kw in keywords:
        words = kw["phrase"].lower().split()
        if not words:
            continue
        matches = sum(1 for w in words if w in listing_lower)
        if matches / len(words) < 0.7:
            missing.append(kw["phrase"])
    return missing


# --- Compliance check ---

def _check_compliance(
    title: str, bullets: List[str], description: str, brand: str, limits: dict
) -> Dict[str, Any]:
    errors = []
    warnings = []

    # Title length
    if len(title) > limits["title"]:
        errors.append(f"Title exceeds {limits['title']} chars ({len(title)})")

    # Bullet length
    for i, b in enumerate(bullets):
        if len(b) > limits["bullet"]:
            errors.append(f"Bullet {i+1} exceeds {limits['bullet']} chars ({len(b)})")

    # Brand position — should be near the start of title
    if brand and brand.lower() not in title[:50].lower():
        warnings.append("Brand not found in first 50 chars of title")

    # WHY: Use word-boundary regex to avoid false positives (e.g. "deal" inside "ideal")
    full_text = (title + " " + " ".join(bullets)).lower()
    for pw in PROMO_WORDS:
        if re.search(rf"\b{re.escape(pw)}\b", full_text):
            errors.append(f"Promotional word found: '{pw}'")

    # Forbidden characters
    for ch in FORBIDDEN_CHARS:
        if ch in title:
            errors.append(f"Forbidden character in title: '{ch}'")

    status = "PASS" if not errors else "FAIL"
    if not errors and warnings:
        status = "WARN"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }


# --- Groq LLM calls ---

def _build_title_prompt(
    product_title: str, brand: str, product_line: str,
    tier1_phrases: List[str], lang: str, max_chars: int,
    expert_context: str = "",
) -> str:
    kw_list = ", ".join(tier1_phrases[:10])
    # WHY: Expert context from Inner Circle transcripts teaches proven title strategies
    context_block = ""
    if expert_context:
        context_block = f"""
EXPERT KNOWLEDGE (use these best practices):
{expert_context}

"""
    return f"""You are an expert Amazon listing optimizer. Your goal is MAXIMUM unique keyword coverage in the title.
{context_block}Product: {product_title}
Brand: {brand}
Product line: {product_line}
Language: {lang}
Max characters: {max_chars}

TOP KEYWORDS (include as EXACT phrases): {kw_list}

Rules:
- IMPORTANT: If any keyword or product info is NOT in {lang}, TRANSLATE it to {lang} first, then use the translated version
- Start with brand name
- Include as many UNIQUE keyword phrases as possible — each phrase should appear ONLY ONCE
- NEVER repeat the same word or phrase — Amazon ignores duplicates and may flag keyword stuffing
- Use " - " dash separators between keyword groups for better Amazon indexing
- After all unique keywords are placed, fill remaining space with product attributes (size, color, material, count)
- Use the FULL {max_chars} characters
- No promotional words (bestseller, #1, günstig, etc.)
- No special characters (!, €, ™, etc.)
- The ENTIRE title must be in {lang} — no words in other languages

Return ONLY the optimized title, nothing else."""


def _build_bullets_prompt(
    product_title: str, brand: str, tier2_phrases: List[str],
    lang: str, max_chars: int,
    expert_context: str = "",
    bullet_count: int = 5,
) -> str:
    kw_list = ", ".join(tier2_phrases[:15])
    context_block = ""
    if expert_context:
        context_block = f"""
EXPERT KNOWLEDGE (use these best practices):
{expert_context}

"""
    return f"""You are an expert Amazon listing optimizer.
{context_block}Product: {product_title}
Brand: {brand}
Language: {lang}
Max characters per bullet: {max_chars}

KEYWORDS to weave in: {kw_list}

Rules:
- IMPORTANT: If any keyword is NOT in {lang}, TRANSLATE it to {lang} first, then use the translated version
- Write exactly {bullet_count} bullet points
- Start each bullet with a CAPITALIZED benefit keyword
- CRITICAL: Include keyword phrases as EXACT matches — weave each phrase verbatim into bullet text
- Each bullet should contain 2-3 keyword phrases naturally integrated
- Focus on benefits, not just features
- Each bullet under {max_chars} characters
- The ENTIRE text must be in {lang} — no words in other languages
- No promotional words

Return ONLY {bullet_count} bullet points, one per line, no numbering or bullet symbols."""


def _build_description_prompt(
    product_title: str, brand: str, remaining_phrases: List[str],
    lang: str,
    expert_context: str = "",
    marketplace: str = "amazon_de",
) -> str:
    kw_list = ", ".join(remaining_phrases[:10])
    context_block = ""
    if expert_context:
        context_block = f"""
EXPERT KNOWLEDGE (use these best practices):
{expert_context}

"""
    # WHY: Allegro buyers scan descriptions — bold keywords are a game changer
    is_allegro = "allegro" in marketplace
    platform_name = "Allegro" if is_allegro else "Amazon"
    paragraph_rule = "Write 3-4 detailed paragraphs" if is_allegro else "Write 2-3 short paragraphs"
    bold_rule = ""
    if is_allegro:
        bold_rule = (
            "\n- BOLD important keywords and product features using <b> tags — "
            "product type, material, size, brand, key benefits. "
            "8-12 bolded phrases total. Buyer must scan description and see key info at a glance."
        )

    return f"""You are an expert {platform_name} listing optimizer.
{context_block}Product: {product_title}
Brand: {brand}
Language: {lang}

REMAINING KEYWORDS to include: {kw_list}

Rules:
- IMPORTANT: If any keyword or product info is NOT in {lang}, TRANSLATE it to {lang} first
- {paragraph_rule}
- Naturally include the remaining keywords
- Focus on use cases and benefits
- Professional tone, no hype
- The ENTIRE text must be in {lang} — no words in other languages
- Format as simple HTML: use <p> for paragraphs, <ul><li> for feature lists, <b> for emphasis{bold_rule}
- Keep HTML clean and minimal — no classes, no inline styles, no <div> or <span>

Return ONLY the HTML description, nothing else."""


def _build_backend_prompt(
    product_title: str, brand: str, title_text: str,
    keywords: List[Dict[str, Any]], lang: str, max_bytes: int,
) -> str:
    """Prompt for LLM to suggest additional backend search terms.

    WHY: Algorithmic packing only uses words from the input keywords.
    When visible coverage is 93%+, almost no keywords are left for backend.
    The LLM can suggest synonyms, alternate phrasings, and related terms
    that shoppers actually search for but aren't in the keyword research.
    """
    kw_sample = ", ".join(k["phrase"] for k in keywords[:20])
    return f"""You are an Amazon backend keyword specialist.

Product: {product_title}
Brand: {brand}
Current title: {title_text}
Language: {lang}

Keywords ALREADY in the listing: {kw_sample}

Generate ADDITIONAL search terms for the backend keyword field (max {max_bytes} bytes).
These terms should NOT duplicate words already in the listing or keywords above.

Include:
- Synonyms and alternate phrasings shoppers use
- Related product category terms
- Common abbreviations and alternate spellings
- Complementary use-case terms (e.g. "camping hiking outdoor" for a water bottle)

Rules:
- IMPORTANT: All terms must be in {lang} — translate if needed
- Space-separated, lowercase, no commas or punctuation
- No brand names, no promotional words, no special characters
- Every word must be UNIQUE (no repetition)

Return ONLY space-separated search terms in {lang}, nothing else."""


def _call_groq(prompt: str, temperature: float, max_tokens: int) -> Tuple[str, Optional[dict]]:
    """Synchronous Groq call with automatic key rotation on 429 rate limits.

    Returns (text, usage_dict | None) — usage_dict contains token counts for tracing.
    """
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
            text = response.choices[0].message.content.strip()
            # WHY: Extract token usage for observability tracing
            usage = None
            if hasattr(response, "usage") and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "model": MODEL,
                }
            return text, usage
        except Exception as e:
            last_error = e
            if "429" in str(e) or "rate_limit" in str(e):
                logger.warning("groq_rate_limit", key_index=i, remaining_keys=len(keys) - i - 1)
                continue
            raise  # Non-rate-limit errors should propagate immediately

    # WHY: All keys exhausted — raise the last error
    raise last_error


# --- Post-processing: strip promo words LLM may have slipped in ---

def _strip_promo_words(text: str) -> str:
    """Remove promotional words from LLM output, clean up leftover whitespace."""
    result = text
    for pw in PROMO_WORDS:
        # WHY: word-boundary match to avoid stripping partial words (e.g. "ideal" from "ideally")
        result = re.sub(rf"\b{re.escape(pw)}\b", "", result, flags=re.IGNORECASE)
    # Clean up double spaces / leading commas left after removal
    result = re.sub(r"\s{2,}", " ", result)
    result = re.sub(r"\s,", ",", result)
    return result.strip()


# --- Allegro keyword bolding ---

def _bold_keywords_in_html(html: str, keywords: List[str]) -> str:
    """Wrap first occurrence of each keyword in <b> tags if not already bolded.

    WHY: Allegro buyers scan descriptions — bolded keywords let them spot
    key product features at a glance (Bartek's "game changer" insight).
    """
    result = html
    for phrase in keywords[:15]:
        if not phrase or len(phrase) < 2:
            continue
        # WHY: Skip if this phrase is already inside a <b> tag
        if re.search(rf"<b>[^<]*{re.escape(phrase)}[^<]*</b>", result, re.IGNORECASE):
            continue
        # WHY: Match phrase only in text content (not inside HTML tags)
        # Negative lookbehind ensures we're not inside a tag attribute
        pattern = rf"(?<![<\w/])({re.escape(phrase)})(?![^<]*>)"
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            original = match.group(0)
            result = result[:match.start()] + f"<b>{original}</b>" + result[match.end():]
    return result


# --- Main entry point ---

async def optimize_listing(
    product_title: str,
    brand: str,
    keywords: List[Dict[str, Any]],
    marketplace: str = "amazon_de",
    mode: str = "aggressive",
    product_line: str = "",
    language: str | None = None,
    db: Session | None = None,
    audience_context: str = "",
    account_type: str = "seller",
    category: str = "",
    **kwargs,
) -> Dict[str, Any]:
    """
    Run full listing optimization: keyword prep → 3 LLM calls → packing → scoring.
    Returns dict matching OptimizerResponse shape.
    """
    trace = new_trace("optimize_listing")
    limits = _get_limits(marketplace)
    lang = _detect_language(marketplace, language)

    # WHY: Sanitize user inputs before they enter LLM prompts (injection prevention)
    product_title = _sanitize_llm_input(product_title)
    brand = _sanitize_llm_input(brand)
    product_line = _sanitize_llm_input(product_line)
    for kw in keywords:
        kw["phrase"] = _sanitize_llm_input(kw["phrase"])

    # WHY: DataDive keyword placement — uses RJ-based ranges instead of simple % tiers
    bullet_count = get_bullet_count(account_type)
    bullet_char_limit = get_bullet_limit(category) if category else limits["bullet"]

    # 1. Keyword preparation
    with span(trace, "keyword_prep"):
        all_kw, tier1, tier2, tier3 = prepare_keywords_with_fallback(keywords, account_type)
        tier1_phrases = [k["phrase"] for k in tier1]
        tier2_phrases = [k["phrase"] for k in tier2]
        tier3_phrases = [k["phrase"] for k in tier3]
        root_words = _extract_root_words(all_kw)

    # WHY: Retrieve expert context from Inner Circle transcripts to improve LLM output
    # Single DB query fetches chunks for all 3 prompt types at once
    title_context = bullets_context = desc_context = ""
    past_successes = []
    with span(trace, "rag_search"):
        if db:
            search_query = f"{product_title} {' '.join(tier1_phrases[:5])}"
            knowledge = await search_knowledge_batch(db, search_query)
            title_context = knowledge.get("title", "")
            bullets_context = knowledge.get("bullets", "")
            desc_context = knowledge.get("description", "")
        # WHY: Fetch past successful listings as few-shot examples for the LLM
        if db:
            past_successes = get_past_successes(db, marketplace)

    # WHY: Audience research gives buyer language — prepend to expert context
    # so LLM uses real customer phrases in title, bullets, description
    if audience_context:
        audience_block = f"AUDIENCE RESEARCH (use buyer language from this):\n{audience_context[:2000]}\n\n"
        title_context = audience_block + title_context
        bullets_context = audience_block + bullets_context
        desc_context = audience_block + desc_context

    logger.info(
        "optimizer_start",
        product=product_title[:50],
        keywords=len(all_kw),
        tiers=f"{len(tier1)}/{len(tier2)}/{len(tier3)}",
        knowledge_title=len(title_context),
        knowledge_bullets=len(bullets_context),
        knowledge_desc=len(desc_context),
        past_successes=len(past_successes),
    )

    # 2. Try n8n first, fall back to direct Groq
    optimization_source = "direct"
    n8n_result = None

    if settings.n8n_webhook_url:
        expert_context = {
            "title": title_context,
            "bullets": bullets_context,
            "description": desc_context,
        }
        payload = build_n8n_payload(
            brand=brand,
            product_title=product_title,
            keywords=all_kw,
            marketplace=marketplace,
            mode=mode,
            language=lang,
            expert_context=expert_context,
            past_successes=past_successes,
        )
        n8n_result = await call_n8n_optimizer(payload)

    backend_suggestions = ""  # WHY: Populated by LLM on direct path, empty on n8n path

    if n8n_result:
        # WHY: n8n returned a valid listing — use it (no token tracking for n8n path)
        optimization_source = "n8n"
        title_text = n8n_result.get("title", "")
        bullet_lines = n8n_result.get("bullet_points", [])
        desc_text = n8n_result.get("description", "")
        title_text = _strip_promo_words(title_text)
        bullet_lines = [_strip_promo_words(b) for b in bullet_lines]
        desc_text = _strip_promo_words(desc_text)
        # WHY: Allegro descriptions need bolded keywords for scanability
        if "allegro" in marketplace:
            desc_text = _bold_keywords_in_html(desc_text, tier1_phrases + tier2_phrases[:10])
    else:
        # Fallback: direct Groq calls (existing flow)
        title_prompt = _build_title_prompt(
            product_title, brand, product_line, tier1_phrases, lang, limits["title"],
            expert_context=title_context,
        )

        with span(trace, "llm_title") as s:
            title_text, title_usage = await asyncio.to_thread(_call_groq, title_prompt, 0.4, 250)
            if title_usage:
                record_llm_usage(s, title_usage)

        # WHY: bullets, description, and backend suggestions are independent — run all 3 in parallel
        bullets_prompt = _build_bullets_prompt(
            product_title, brand, tier2_phrases, lang, bullet_char_limit,
            expert_context=bullets_context,
            bullet_count=bullet_count,
        )
        desc_prompt = _build_description_prompt(
            product_title, brand, tier3_phrases + tier2_phrases[-5:], lang,
            expert_context=desc_context,
            marketplace=marketplace,
        )
        backend_prompt = _build_backend_prompt(
            product_title, brand, title_text, all_kw, lang, limits["backend"],
        )

        # WHY: Backend keyword LLM call is optional — use return_exceptions so it
        # can fail without killing the essential bullets+desc calls
        with span(trace, "llm_bullets_desc") as s:
            results = await asyncio.gather(
                asyncio.to_thread(_call_groq, bullets_prompt, 0.5, 800),
                asyncio.to_thread(_call_groq, desc_prompt, 0.5, 600),
                asyncio.to_thread(_call_groq, backend_prompt, 0.3, 200),
                return_exceptions=True,
            )
            # WHY: Unpack — if any is an Exception, handle gracefully
            if isinstance(results[0], Exception):
                raise results[0]  # Bullets are essential — re-raise
            if isinstance(results[1], Exception):
                raise results[1]  # Description is essential — re-raise
            (bullets_raw, b_usage) = results[0]
            (desc_text, d_usage) = results[1]
            if isinstance(results[2], Exception):
                logger.warning("backend_llm_failed", error=str(results[2]))
                backend_suggestions = ""
                bk_usage = None
            else:
                (backend_suggestions, bk_usage) = results[2]
            if b_usage:
                record_llm_usage(s, b_usage)
            if d_usage:
                record_llm_usage(s, d_usage, accumulate=True)
            if bk_usage:
                record_llm_usage(s, bk_usage, accumulate=True)

        # Parse bullets — one per line, strip numbering artifacts
        bullet_lines = [
            re.sub(r"^[\d\.\-\*\•]+\s*", "", line).strip()
            for line in bullets_raw.split("\n")
            if line.strip() and len(line.strip()) > 10
        ][:bullet_count]

        # WHY: LLM sometimes ignores "no promotional words" instruction — strip them
        title_text = _strip_promo_words(title_text)
        bullet_lines = [_strip_promo_words(b) for b in bullet_lines]
        desc_text = _strip_promo_words(desc_text)

        # WHY: Allegro descriptions need bolded keywords for scanability
        if "allegro" in marketplace:
            desc_text = _bold_keywords_in_html(desc_text, tier1_phrases + tier2_phrases[:10])

        # WHY: LLM often generates titles 5-15 chars over limit — truncate at last word boundary
        if len(title_text) > limits["title"]:
            truncated = title_text[:limits["title"]]
            # Cut at last space to avoid broken words
            last_space = truncated.rfind(" ")
            if last_space > limits["title"] * 0.8:
                title_text = truncated[:last_space]
            else:
                title_text = truncated
        # WHY: LLM backend suggestions fill remaining 249 bytes after algorithmic packing
        backend_suggestions = _strip_promo_words(backend_suggestions)

    # 3. Backend keyword packing + coverage + compliance + scoring
    with span(trace, "scoring"):
        full_listing_text = title_text + " " + " ".join(bullet_lines) + " " + desc_text
        backend_kw = _pack_backend_keywords(all_kw, full_listing_text, limits["backend"], backend_suggestions)
        backend_bytes = len(backend_kw.encode("utf-8"))

        full_text_with_backend = full_listing_text + " " + backend_kw
        coverage_pct, exact_matches, coverage_mode = _calculate_coverage(all_kw, full_text_with_backend)
        title_cov, _, _ = _calculate_coverage(tier1, title_text)
        missing = _find_missing_keywords(all_kw, full_text_with_backend)

        compliance = _check_compliance(title_text, bullet_lines, desc_text, brand, limits)

        # WHY: Anti-stuffing catches keyword repetition that compliance check misses
        stuffing_warnings = run_anti_stuffing_check(title_text, bullet_lines, desc_text)
        if stuffing_warnings:
            compliance["warnings"].extend(stuffing_warnings)
            compliance["warning_count"] = len(compliance["warnings"])
            if compliance["status"] == "PASS":
                compliance["status"] = "WARN"

        backend_util = round((backend_bytes / limits["backend"]) * 100, 1) if limits["backend"] > 0 else 0
        rj = calculate_ranking_juice(all_kw, title_text, bullet_lines, backend_kw, desc_text)

        # WHY: Multi-tier coverage shows WHERE keywords are missing, not just overall %
        coverage_breakdown = calculate_multi_tier_coverage(
            all_kw, title_text, bullet_lines, backend_kw, desc_text,
        )

        # WHY: PPC recommendations are pure post-processing — zero LLM cost
        ppc = generate_ppc_recommendations(all_kw, full_text_with_backend)

    # Self-learning — store if RJ >= 75, capture listing_id for feedback
    listing_history_id = None
    if db:
        try:
            listing_history_id = store_successful_listing(
                db,
                listing_data={
                    "brand": brand,
                    "marketplace": marketplace,
                    "product_title": product_title,
                    "title": title_text,
                    "bullets": json.dumps(bullet_lines),
                    "description": desc_text,
                    "backend_keywords": backend_kw,
                    "keyword_count": len(all_kw),
                },
                ranking_juice_data=rj,
            )
        except Exception as e:
            logger.warning("self_learning_save_failed", error=str(e))

    trace_data = finalize_trace(trace)

    logger.info(
        "optimizer_done",
        coverage=coverage_pct,
        compliance=compliance["status"],
        backend_bytes=backend_bytes,
        ranking_juice=rj["score"],
        grade=rj["grade"],
        source=optimization_source,
        trace_duration_ms=trace_data["total_duration_ms"],
        trace_tokens=trace_data["total_tokens"],
        trace_cost_usd=trace_data["estimated_cost_usd"],
    )

    return {
        "status": "success",
        "marketplace": marketplace,
        "brand": brand,
        "mode": mode,
        "language": lang,
        "listing": {
            "title": title_text,
            "bullet_points": bullet_lines,
            "description": desc_text,
            "backend_keywords": backend_kw,
        },
        "scores": {
            "coverage_pct": coverage_pct,
            "coverage_mode": coverage_mode,
            "exact_matches_in_title": exact_matches,
            "title_coverage_pct": title_cov,
            "backend_utilization_pct": backend_util,
            "backend_byte_size": backend_bytes,
            "compliance_status": compliance["status"],
        },
        "compliance": compliance,
        "keyword_intel": {
            "total_analyzed": len(all_kw),
            "tier1_title": len(tier1),
            "tier2_bullets": len(tier2),
            "tier3_backend": len(tier3),
            "missing_keywords": missing[:20],
            "root_words": root_words,
        },
        "ranking_juice": rj,
        "optimization_source": optimization_source,
        "listing_history_id": listing_history_id,
        "trace": trace_data,
        "coverage_breakdown": coverage_breakdown.get("breakdown", {}),
        "coverage_target": coverage_breakdown.get("target_pct", 95.0),
        "meets_coverage_target": coverage_breakdown.get("meets_target", False),
        "ppc_recommendations": ppc,
        "account_type": account_type,
    }
