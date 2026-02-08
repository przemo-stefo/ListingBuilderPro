# backend/services/scraper/pyrox_linkedin/models.py
# Purpose: Data classes for LinkedIn scraper (company, decision maker, lead)
# NOT for: Scraping logic — see strategies.py, playwright_scraper.py

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class LinkedInCompany:
    """Extracted company data from LinkedIn"""
    url: str
    name: str = ""
    website: str = ""
    industry: str = ""
    location: str = ""
    country: str = ""
    size: str = ""
    description: str = ""
    specialties: List[str] = field(default_factory=list)
    scraper_used: str = ""


@dataclass
class DecisionMaker:
    """Decision maker found at a company"""
    name: str
    designation: str
    linkedin_url: str = ""
    email: str = ""
    company: str = ""
    priority: int = 0
    best_approach: str = ""


@dataclass
class PyroxLead:
    """Final lead ready for Sales Agent pipeline"""
    name: str
    email: str
    company: str
    website: str
    designation: str
    linkedin_url: str
    industry: str
    country: str
    pyrox_score: int = 0
    best_approach: str = ""
    source: str = "pyrox-linkedin-scraper"
    scraped_at: str = ""

    def to_webhook_payload(self) -> Dict:
        """Format for n8n Sales Agent webhook POST"""
        return {
            "name": self.name,
            "email": self.email,
            "company": self.company,
            "website": self.website,
            "message": (
                f"Auto-generated lead from PYROX LinkedIn Scraper. "
                f"Industry: {self.industry}. Country: {self.country}. "
                f"Role: {self.designation}. LinkedIn: {self.linkedin_url}. "
                f"Best approach: {self.best_approach}"
            )
        }
