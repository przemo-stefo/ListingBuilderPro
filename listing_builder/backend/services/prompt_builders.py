# backend/services/prompt_builders.py
# Purpose: LLM prompt templates for title, bullets, description, backend keywords
# NOT for: LLM calls, scoring, or keyword logic (those stay in optimizer_service.py)

from __future__ import annotations

from typing import List, Dict, Any
from services.category_prompts import get_category_rules

# WHY: Rules from Inner Circle knowledge + Amazon algorithm research (4-layer search model)
# Injected ONLY for amazon marketplaces — other platforms have different best practices
AMAZON_TITLE_RULES = """
AMAZON-SPECIFIC TITLE RULES:
- Start with brand name, then front-load the HIGHEST VOLUME exact-match keyword
- Mobile shows only 70-90 characters — put critical keywords FIRST
- Use " - " dash separators between keyword groups for better indexing
- Never repeat the same word — Amazon treats singular/plural as the same root
- Title must be readable for the customer, not a keyword dump
- Capitalize all words except prepositions and conjunctions
- Every ROOT WORD must appear somewhere in the listing — missing roots = indexing holes
"""

AMAZON_BULLETS_RULES = """
AMAZON-SPECIFIC BULLET RULES:
- Structure: [CAPS BENEFIT HEADER] - [Feature -> Advantage -> Benefit with keywords]
- Strongest bullet on top — shoppers read top 2-3 only on mobile (first ~150 chars visible)
- Weave 2-3 keyword phrases per bullet NATURALLY — each bullet targets different root word routes
- Use concrete benefits: "saves 2h/week" NOT "highest quality"
- Target different customer avatars per bullet (eco-conscious, busy parent, gift shopper, etc.)
- Include SECONDARY root words not in the title — bullets are the #2 SEO tool after title
- Optimal length: 200-250 chars per bullet
"""

AMAZON_DESC_RULES = """
AMAZON-SPECIFIC DESCRIPTION RULES:
- Structure: Intro -> Summarize bullet benefits -> Brand message -> Subtle CTA
- Each keyword should appear ONCE only — repetition degrades ranking!
- Use synonyms for words already in title/bullets — this feeds Amazon's semantic matching layer
- Max 2000 characters, natural conversational language
- Focus on use cases and lifestyle benefits — Amazon's BERT layer understands context and buyer intent
- Write comprehensive, natural text — it helps Amazon's contextual matching beyond exact keywords
"""

AMAZON_BACKEND_RULES = """
AMAZON-SPECIFIC BACKEND KEYWORD RULES:
- 250 bytes max, all lowercase, space-separated
- NEVER include competitor ASINs or brand names (permanent ban risk!)
- Include common misspellings shoppers actually type
- Only words NOT ALREADY in visible listing (title, bullets, description)
- No commas, no punctuation, no repeated words
- Include foreign-language synonyms and alternate spellings (feeds semantic matching)
- Include complementary use-case terms — Amazon's behavioral layer links related products
- Fill ALL remaining root words not covered by title/bullets — no indexing holes
"""


def build_title_prompt(
    product_title: str, brand: str, product_line: str,
    tier1_phrases: List[str], lang: str, max_chars: int,
    expert_context: str = "",
    marketplace: str = "",
    category: str = "",
) -> str:
    kw_list = ", ".join(tier1_phrases[:10])
    # WHY: Expert context from knowledge base teaches proven title strategies
    context_block = ""
    if expert_context:
        context_block = f"""
EXPERT KNOWLEDGE (use these best practices):
{expert_context}

"""
    # WHY: Algorithm insight only relevant for Amazon — Allegro/eBay have different ranking models
    algo_insight = ""
    if marketplace.startswith("amazon"):
        algo_insight = """
AMAZON SEARCH ALGORITHM INSIGHT: Amazon matches titles through 4 layers — exact text match (most weight in first 150 chars), semantic meaning, contextual understanding (BERT), and buyer behavior patterns. Front-loading exact-match keywords maximizes the strongest signal.
"""
    return f"""You are an expert Amazon listing optimizer. Your goal is MAXIMUM unique keyword coverage in the title.
{algo_insight}
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
{AMAZON_TITLE_RULES if marketplace.startswith("amazon") else ""}
{get_category_rules(category, "title")}
Return ONLY the optimized title, nothing else."""


def build_bullets_prompt(
    product_title: str, brand: str, tier2_phrases: List[str],
    lang: str, max_chars: int,
    expert_context: str = "",
    bullet_count: int = 5,
    marketplace: str = "",
    category: str = "",
) -> str:
    kw_list = ", ".join(tier2_phrases[:15])
    context_block = ""
    if expert_context:
        context_block = f"""
EXPERT KNOWLEDGE (use these best practices):
{expert_context}

"""
    # WHY: Vendor (10 bullets) needs different guidance — more keywords to spread,
    # each bullet should be substantial (120-200 chars) with real benefit copy
    vendor_guidance = ""
    if bullet_count > 5:
        vendor_guidance = f"""
- You have {bullet_count} bullets — spread keywords evenly, 1-2 phrases per bullet
- Each bullet MUST be 120-{max_chars} characters — write full sentences with real product benefits
- DO NOT write short keyword-only bullets — Amazon penalizes thin content
- Group bullets by theme: material, durability, design, use cases, care instructions, specs"""

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
- Include keyword phrases naturally — weave each phrase into real benefit-driven copy
- Each bullet should contain 1-3 keyword phrases integrated into meaningful sentences
- Focus on benefits, not just features — explain WHY the feature matters to the buyer
- Each bullet MUST be between 100 and {max_chars} characters — use the full space
- The ENTIRE text must be in {lang} — no words in other languages
- No promotional words{vendor_guidance}
{AMAZON_BULLETS_RULES if marketplace.startswith("amazon") else ""}
{get_category_rules(category, "bullets")}
Return ONLY {bullet_count} bullet points, one per line, no numbering or bullet symbols."""


def build_description_prompt(
    product_title: str, brand: str, remaining_phrases: List[str],
    lang: str,
    expert_context: str = "",
    marketplace: str = "amazon_de",
    category: str = "",
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
    # WHY: Bartek (16.02) — Allegro opisy powinny mieć ~1000 znaków, 3 akapity
    paragraph_rule = "Write exactly 3 detailed paragraphs, target 800-1200 characters of text (excluding HTML tags)" if is_allegro else "Write 2-3 short paragraphs"
    bold_rule = ""
    if is_allegro:
        bold_rule = (
            "\n- BOLD important keywords and product features using <b> tags — "
            "product type, material, size, brand, key benefits. "
            "8-12 bolded phrases total. Buyer must scan description and see key info at a glance."
        )

    # WHY: Description feeds Amazon's BERT contextual layer — natural, comprehensive text
    # helps Amazon understand product intent even beyond exact keyword matches
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
{AMAZON_DESC_RULES if "amazon" in marketplace else ""}
{get_category_rules(category, "description")}
Return ONLY the HTML description, nothing else."""


def build_backend_prompt(
    product_title: str, brand: str, title_text: str,
    keywords: List[Dict[str, Any]], lang: str, max_bytes: int,
    marketplace: str = "",
    category: str = "",
) -> str:
    """Prompt for LLM to suggest additional backend search terms.

    WHY: Algorithmic packing only uses words from the input keywords.
    When visible coverage is 93%+, almost no keywords are left for backend.
    The LLM can suggest synonyms, alternate phrasings, and related terms
    that shoppers actually search for but aren't in the keyword research.
    """
    kw_sample = ", ".join(k["phrase"] for k in keywords[:20])
    # WHY: Indexing insight only useful for Amazon — other platforms handle backend differently
    indexing_insight = ""
    if marketplace.startswith("amazon"):
        indexing_insight = """
INDEXING INSIGHT: Backend keywords are the last chance to cover root words missing from visible listing. Amazon uses 4 matching layers — backend feeds the lexical and semantic layers. Every uncovered root word = a keyword family you CANNOT rank for.
"""
    return f"""You are an Amazon backend keyword specialist.
{indexing_insight}
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
- Foreign-language terms buyers might search in (feeds semantic matching)

Rules:
- IMPORTANT: All terms must be in {lang} — translate if needed
- Space-separated, lowercase, no commas or punctuation
- No brand names, no promotional words, no special characters
- Every word must be UNIQUE (no repetition)
{AMAZON_BACKEND_RULES if marketplace.startswith("amazon") else ""}
{get_category_rules(category, "backend")}
Return ONLY space-separated search terms in {lang}, nothing else."""
