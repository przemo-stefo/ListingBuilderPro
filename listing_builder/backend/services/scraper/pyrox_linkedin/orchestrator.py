# backend/services/scraper/pyrox_linkedin/orchestrator.py
# Purpose: Main PyroxLinkedInScraper with failover logic and n8n integration
# NOT for: Individual scraping strategies — see strategies.py, playwright_scraper.py

import asyncio
import logging
import os
from dataclasses import asdict
from datetime import datetime
from typing import List, Optional, Dict

import aiohttp

from .models import LinkedInCompany, PyroxLead
from .qualification import calculate_pyrox_score
from .strategies import DirectHTTPLinkedIn, ScraperAPILinkedIn
from .playwright_scraper import PlaywrightLinkedInScraper

logger = logging.getLogger(__name__)


class PyroxLinkedInScraper:
    """
    Main scraper with automatic failover between strategies.

    Order: Direct HTTP → Playwright → ScraperAPI

    Usage:
        scraper = PyroxLinkedInScraper()
        leads = await scraper.scrape_company_leads("https://linkedin.com/company/freshfields")
        for lead in leads:
            payload = lead.to_webhook_payload()
    """

    def __init__(
        self,
        scraperapi_key: Optional[str] = None,
        headless: bool = True,
        use_playwright: bool = True,
        use_scraperapi: bool = True,
    ):
        self.headless = headless
        self.use_playwright = use_playwright
        self.scraperapi_key = scraperapi_key or os.getenv('SCRAPERAPI_KEY')
        self.use_scraperapi = use_scraperapi and bool(self.scraperapi_key)
        self._playwright_scraper = None

    def _has_enough_data(self, company: LinkedInCompany) -> bool:
        """Check if scrape got enough data for reliable scoring"""
        if not company.name:
            return False
        has_industry = bool(company.industry)
        has_location = bool(company.country or company.location)
        has_size = bool(company.size)
        return has_industry or has_location or has_size

    async def scrape_company(self, linkedin_url: str) -> LinkedInCompany:
        """Scrape company with automatic failover: Direct → Playwright → ScraperAPI"""
        errors = []

        # Strategy 1: Direct HTTP (free, fast)
        try:
            direct = DirectHTTPLinkedIn()
            company = await direct.scrape_company(linkedin_url)
            if self._has_enough_data(company):
                return company
            logger.info("Direct got name only, escalating to Playwright...")
        except Exception as e:
            errors.append(f"Direct: {e}")
            logger.info("Direct failed, trying Playwright...")

        # Strategy 2: Playwright (free, anti-detection)
        if self.use_playwright:
            try:
                if not self._playwright_scraper:
                    self._playwright_scraper = PlaywrightLinkedInScraper(headless=self.headless)
                company = await self._playwright_scraper.scrape_company(linkedin_url)
                if self._has_enough_data(company):
                    return company
                logger.info("Playwright got thin data, trying ScraperAPI...")
            except Exception as e:
                errors.append(f"Playwright: {e}")
                logger.info("Playwright failed, trying ScraperAPI...")

        # Strategy 3: ScraperAPI (paid, most reliable)
        if self.use_scraperapi:
            try:
                scraper_api = ScraperAPILinkedIn(api_key=self.scraperapi_key)
                company = await scraper_api.scrape_company(linkedin_url)
                if company.name:
                    return company
            except Exception as e:
                errors.append(f"ScraperAPI: {e}")

        logger.error(f"All scraping strategies failed for {linkedin_url}: {errors}")
        return LinkedInCompany(
            url=linkedin_url,
            description=f"Scraping failed: {'; '.join(errors)}",
            scraper_used="none"
        )

    async def scrape_company_leads(
        self, linkedin_url: str, min_score: int = 4,
    ) -> List[PyroxLead]:
        """Full pipeline: scrape company → qualify → build leads"""
        now = datetime.now().isoformat()

        logger.info(f"Step 1: Scraping company {linkedin_url}")
        company = await self.scrape_company(linkedin_url)

        score = calculate_pyrox_score(company)
        logger.info(f"Step 2: Pyrox score = {score}/10 for {company.name}")

        if score < min_score:
            logger.info(f"Score {score} < {min_score}, skipping {company.name}")
            return []

        return [
            PyroxLead(
                name=f"Decision Maker at {company.name}",
                email="",
                company=company.name,
                website=company.website,
                designation="",
                linkedin_url=linkedin_url,
                industry=company.industry,
                country=company.country or company.location,
                pyrox_score=score,
                best_approach=self._determine_approach(company, score),
                scraped_at=now,
            )
        ]

    async def scrape_multiple(
        self, urls: List[str], delay: float = 3.0, min_score: int = 4,
    ) -> List[PyroxLead]:
        """Scrape multiple companies with rate limiting"""
        all_leads = []

        for i, url in enumerate(urls, 1):
            logger.info(f"\n[{i}/{len(urls)}] {url}")
            try:
                leads = await self.scrape_company_leads(url, min_score=min_score)
                all_leads.extend(leads)
                logger.info(f"  Found {len(leads)} leads (score >= {min_score})")
            except Exception as e:
                logger.error(f"  Error: {e}")

            if i < len(urls):
                logger.info(f"  Waiting {delay}s...")
                await asyncio.sleep(delay)

        logger.info(f"\nTotal: {len(all_leads)} qualified leads from {len(urls)} companies")
        return all_leads

    async def send_to_n8n(
        self,
        leads: List[PyroxLead],
        webhook_url: str = "http://localhost:5678/webhook/ai-sales-agent",
    ) -> List[Dict]:
        """Send leads to n8n Sales Agent webhook"""
        responses = []

        async with aiohttp.ClientSession() as session:
            for lead in leads:
                payload = lead.to_webhook_payload()
                try:
                    async with session.post(
                        webhook_url, json=payload,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        result = await response.json()
                        responses.append(result)
                        logger.info(f"Sent to n8n: {lead.company} - {response.status}")
                except Exception as e:
                    logger.error(f"Failed to send {lead.company}: {e}")
                    responses.append({"error": str(e)})
                await asyncio.sleep(0.5)

        return responses

    def _determine_approach(self, company: LinkedInCompany, score: int) -> str:
        """Determine best sales angle based on company data"""
        desc = (company.description + " " + company.industry).lower()

        if any(w in desc for w in ["gdpr", "data protection", "datenschutz", "compliance"]):
            return "gdpr_sovereignty"
        elif any(w in desc for w in ["law", "legal", "rechtsanwalt", "kanzlei"]):
            return "legal_ai_compliance"
        elif any(w in desc for w in ["finance", "financial", "banking", "bank", "insurance", "versicherung"]):
            return "financial_data_sovereignty"
        elif any(w in desc for w in ["cloud", "aws", "azure", "openai"]):
            return "cost_savings_vs_cloud"
        elif any(w in desc for w in ["healthcare", "medical", "pharma"]):
            return "healthcare_hipaa_gdpr"
        else:
            return "sovereign_ai_cost_savings"

    async def close(self):
        """Cleanup all resources"""
        if self._playwright_scraper:
            await self._playwright_scraper.close()
