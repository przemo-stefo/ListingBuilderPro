# backend/services/scraper/pyrox_linkedin/__init__.py
# Purpose: Public API for PYROX LinkedIn scraper package
# NOT for: Implementation details — see individual modules

"""
PYROX AI LinkedIn Scraper - Multi-strategy lead generation

3 scraping strategies (automatic failover):
1. Direct HTTP (fast, may get blocked) - FREE
2. Playwright (headless browser, anti-detection) - FREE
3. ScraperAPI (residential proxies) - $49/mo

Target: EU Legal/Financial decision makers (CTO/CIO/CISO/DPO)
Output: JSON leads compatible with n8n Sales Agent webhook
"""

from .models import LinkedInCompany, DecisionMaker, PyroxLead
from .qualification import (
    match_decision_maker_role,
    calculate_pyrox_score,
    TARGET_ROLES,
    TARGET_INDUSTRIES,
    EU_COUNTRIES,
)
from .orchestrator import PyroxLinkedInScraper
from .employee_finder import LinkedInEmployeeFinder
from .server import run_webhook_server

__all__ = [
    "LinkedInCompany",
    "DecisionMaker",
    "PyroxLead",
    "match_decision_maker_role",
    "calculate_pyrox_score",
    "TARGET_ROLES",
    "TARGET_INDUSTRIES",
    "EU_COUNTRIES",
    "PyroxLinkedInScraper",
    "LinkedInEmployeeFinder",
    "run_webhook_server",
]
