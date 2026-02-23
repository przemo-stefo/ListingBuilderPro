# backend/services/prompt_builders.py
# Purpose: LLM prompt templates for title, bullets, description, backend keywords
# NOT for: LLM calls, scoring, or keyword logic (those stay in optimizer_service.py)

from __future__ import annotations

from typing import List, Dict, Any


def build_title_prompt(
    product_title: str, brand: str, product_line: str,
    tier1_phrases: List[str], lang: str, max_chars: int,
    expert_context: str = "",
) -> str:
    kw_list = ", ".join(tier1_phrases[:10])
    # WHY: Expert context from knowledge base teaches proven title strategies
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


def build_bullets_prompt(
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

Return ONLY {bullet_count} bullet points, one per line, no numbering or bullet symbols."""


def build_description_prompt(
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


def build_backend_prompt(
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
