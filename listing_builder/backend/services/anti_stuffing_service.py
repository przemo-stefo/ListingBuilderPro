# backend/services/anti_stuffing_service.py
# Purpose: Detect keyword stuffing — density caps and word repetition limits
# NOT for: LLM calls or keyword placement strategy (that's keyword_placement_service.py)

from __future__ import annotations

import re
from typing import List, Dict, Any


# WHY: Amazon's A10 algorithm penalizes keyword density >3% per word
MAX_DENSITY_PCT = 3.0
# WHY: Repeating a word more than 2x in title looks spammy and triggers suppression
TITLE_MAX_REPEATS = 2
# WHY: Across the full listing, 3x is the safe ceiling per DataDive analysis
LISTING_MAX_REPEATS = 3
# WHY: Skip common function words — they inflate density but aren't keyword stuffing.
# Covers EN/DE/PL/FR/IT/ES since listings are generated in marketplace language.
STOP_WORDS = {
    # English
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "as", "be", "was", "are",
    "not", "no", "can", "will", "has", "have", "do", "does", "so", "if",
    "this", "that", "your", "our", "its", "their", "all", "also", "more",
    # German
    "der", "die", "das", "den", "dem", "des", "und", "oder", "mit", "von",
    "fur", "für", "ein", "eine", "einen", "einem", "einer", "ist", "sind", "hat",
    "sie", "er", "es", "wir", "ihr", "nicht", "auch", "noch", "nur",
    "wird", "werden", "kann", "aus", "bei", "nach", "auf", "sich", "wie",
    "zu", "zum", "zur", "als", "so", "da", "ob", "wenn", "was", "man",
    "durch", "diese", "dieser", "dieses", "mehr", "sehr", "ihre", "ihren",
    "unsere", "unserer", "unserem", "unseren", "dank", "ihrer", "ihrem",
    # Polish
    "z", "w", "na", "do", "i", "lub", "od", "dla", "ze", "po", "nie",
    "to", "jest", "sie", "jak", "co", "ten", "ta", "te", "ich", "tym",
    # French
    "le", "la", "les", "un", "une", "des", "et", "ou", "de", "du", "en",
    "est", "ce", "qui", "que", "pas", "par", "sur", "son", "ses", "aux",
    # Italian
    "il", "lo", "la", "li", "le", "un", "una", "di", "da", "per", "con",
    "che", "non", "del", "dei", "nel", "sul", "suo", "sua",
    # Spanish
    "el", "la", "los", "las", "un", "una", "de", "en", "con", "por",
    "del", "que", "es", "no", "su", "sus", "al", "se", "lo",
}


def _word_counts(text: str) -> Dict[str, int]:
    """Count word occurrences, lowercased, stripped of punctuation."""
    words = re.findall(r"[a-zA-ZäöüßÄÖÜąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+", text.lower())
    counts: Dict[str, int] = {}
    for w in words:
        if len(w) >= 2 and w not in STOP_WORDS:
            counts[w] = counts.get(w, 0) + 1
    return counts


def validate_keyword_density(text: str) -> List[str]:
    """Check no single word exceeds MAX_DENSITY_PCT of total word count."""
    warnings: List[str] = []
    counts = _word_counts(text)
    total = sum(counts.values())
    if total == 0:
        return warnings

    for word, count in counts.items():
        density = (count / total) * 100
        if density > MAX_DENSITY_PCT:
            warnings.append(
                f"Keyword stuffing: '{word}' appears {count}x ({density:.1f}% density, max {MAX_DENSITY_PCT}%)"
            )
    return warnings


def validate_word_repetition(title: str, bullets: List[str]) -> List[str]:
    """Check word repetition limits — title and full listing separately."""
    warnings: List[str] = []

    # Title check
    title_counts = _word_counts(title)
    for word, count in title_counts.items():
        if count > TITLE_MAX_REPEATS:
            warnings.append(
                f"Title repetition: '{word}' appears {count}x (max {TITLE_MAX_REPEATS}x in title)"
            )

    # Full listing check (title + bullets combined)
    full_text = title + " " + " ".join(bullets)
    listing_counts = _word_counts(full_text)
    for word, count in listing_counts.items():
        if count > LISTING_MAX_REPEATS:
            warnings.append(
                f"Listing repetition: '{word}' appears {count}x (max {LISTING_MAX_REPEATS}x in listing)"
            )

    return warnings


def run_anti_stuffing_check(
    title: str, bullets: List[str], description: str,
) -> List[str]:
    """Combined anti-stuffing check — returns list of warning strings."""
    full_text = title + " " + " ".join(bullets) + " " + description
    warnings = validate_keyword_density(full_text)
    warnings.extend(validate_word_repetition(title, bullets))
    return warnings
