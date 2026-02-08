# backend/services/scraper/pyrox_linkedin/qualification.py
# Purpose: Role matching, industry targeting, and Pyrox score calculation
# NOT for: Scraping — see strategies.py, playwright_scraper.py

import re
from typing import Optional

from .models import LinkedInCompany


# Roles we want to find, ordered by priority (1 = highest)
TARGET_ROLES = {
    # C-level (priority 1-3)
    "cto": 1, "chief technology officer": 1,
    "cio": 2, "chief information officer": 2,
    "ciso": 3, "chief information security officer": 3,
    "cdo": 3, "chief data officer": 3,
    # Data protection (priority 4)
    "dpo": 4, "data protection officer": 4,
    "datenschutzbeauftragter": 4,  # German DPO
    # VP level (priority 5)
    "vp of technology": 5, "vp of it": 5, "vp of engineering": 5,
    "vp technology": 5, "vp it": 5, "vp engineering": 5,
    "vice president technology": 5, "vice president it": 5,
    # Head level (priority 6)
    "head of it": 6, "head of technology": 6, "head of engineering": 6,
    "head of data": 6, "head of infrastructure": 6, "head of ai": 6,
    "leiter it": 6, "leiter technologie": 6,  # German
    # Director level (priority 7)
    "it director": 7, "technology director": 7, "director of it": 7,
    "director of engineering": 7, "director of technology": 7,
    # Law firm specific (priority 8)
    "managing partner": 8, "senior partner": 8,
    "geschäftsführer": 8,  # German managing director
    # COO (priority 9)
    "coo": 9, "chief operating officer": 9,
}


def match_decision_maker_role(designation: str) -> Optional[int]:
    """
    Check if a job title matches our target decision maker roles.
    Returns priority (1=highest) or None if not a match.
    """
    if not designation:
        return None

    title_lower = designation.lower().strip()

    for role_key, priority in TARGET_ROLES.items():
        if role_key in title_lower:
            return priority

    return None


# Industries that are ideal Pyrox targets
TARGET_INDUSTRIES = [
    "law", "legal", "rechtsanwalt", "kanzlei", "anwalt",
    "finance", "financial", "banking", "bank", "insurance", "versicherung",
    "healthcare", "health", "medical", "pharma", "gesundheit",
    "accounting", "audit", "consulting",
]

# EU countries (focus DACH) - includes UK sub-regions LinkedIn uses
EU_COUNTRIES = [
    "germany", "deutschland", "austria", "österreich", "switzerland", "schweiz",
    "netherlands", "belgium", "france", "luxembourg", "italy", "spain",
    "poland", "czech", "denmark", "sweden", "finland", "norway",
    "ireland", "portugal", "united kingdom", "uk",
    "england", "scotland", "wales", "northern ireland",  # LinkedIn uses these
    "berlin", "munich", "münchen", "frankfurt", "hamburg", "düsseldorf",  # German cities
    "vienna", "wien", "zurich", "zürich", "amsterdam", "paris", "brussels",  # Major EU cities
    "london", "manchester", "edinburgh", "dublin",  # UK/Ireland cities
    "warsaw", "warszawa", "prague", "praha", "copenhagen", "stockholm",  # Other EU
]


def calculate_pyrox_score(company: LinkedInCompany) -> int:
    """
    Score a company for Pyrox AI fit (1-10).

    Scoring:
    - EU location: +3
    - Legal/Finance/Healthcare: +3
    - AI/cloud mentions in description: +2
    - Company size 50+: +1
    - Has website: +1
    """
    score = 0
    desc_lower = (company.description + " " + company.industry).lower()
    loc_lower = (company.location + " " + company.country).lower()

    # EU presence (+3)
    if any(c in loc_lower for c in EU_COUNTRIES):
        score += 3

    # Target industry (+3)
    if any(ind in desc_lower for ind in TARGET_INDUSTRIES):
        score += 3

    # AI/cloud mentions (+2)
    ai_keywords = [
        "ai", "artificial intelligence", "machine learning", "cloud",
        "data processing", "automation", "digitalization", "digital transformation",
    ]
    if any(kw in desc_lower for kw in ai_keywords):
        score += 2

    # Company size (+1) - strip commas because LinkedIn uses "5,001-10,000"
    size_clean = company.size.lower().replace(",", "")
    size_match = re.search(r'(\d+)', size_clean)
    if size_match:
        emp_count = int(size_match.group(1))
        if emp_count >= 50:
            score += 1

    # Has website (+1)
    if company.website and company.website != "":
        score += 1

    return min(score, 10)
