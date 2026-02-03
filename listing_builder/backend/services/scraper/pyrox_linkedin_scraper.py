# backend/services/scraper/pyrox_linkedin_scraper.py
# Purpose: Scrape LinkedIn company pages + employees for PYROX AI lead generation
# NOT for: Allegro scraping (use allegro_scraper.py) or news (use aggregator)

"""
PYROX AI LinkedIn Scraper - Multi-strategy lead generation

Reuses anti-detection patterns from allegro_scraper_playwright.py
and ScraperAPI fallback from allegro_scraper_with_scraperapi.py.

3 scraping strategies (automatic failover):
1. Playwright (headless browser, anti-detection) - FREE
2. ScraperAPI (residential proxies) - $49/mo
3. Direct HTTP (fast, may get blocked) - FREE

Target: EU Legal/Financial decision makers (CTO/CIO/CISO/DPO)
Output: JSON leads compatible with n8n Sales Agent webhook
"""

import asyncio
import aiohttp
import json
import re
import os
import random
import logging
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

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


# ============================================================================
# DECISION MAKER ROLE DETECTION
# ============================================================================

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

    # Exact and partial matching
    for role_key, priority in TARGET_ROLES.items():
        if role_key in title_lower:
            return priority

    return None


# ============================================================================
# PYROX QUALIFICATION
# ============================================================================

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
    - Company size 50-5000: +1
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
    ai_keywords = ["ai", "artificial intelligence", "machine learning", "cloud",
                    "data processing", "automation", "digitalization", "digital transformation"]
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


# ============================================================================
# STRATEGY 1: PLAYWRIGHT (anti-detection browser)
# ============================================================================

class PlaywrightLinkedInScraper:
    """
    Scrape LinkedIn using Playwright with anti-detection.

    Reuses patterns from allegro_scraper_playwright.py:
    - navigator.webdriver override
    - Custom user agent and locale
    - Timezone spoofing
    - Viewport simulation
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.playwright = None

    async def _init_browser(self):
        """Initialize browser with anti-detection settings"""
        if self.browser:
            return

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright not installed. Run:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            )

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )

    async def _create_context(self):
        """Create browser context with stealth settings for EU browsing"""
        context = await self.browser.new_context(
            locale='en-GB',
            viewport={'width': 1920, 'height': 1080},
            user_agent=(
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/131.0.0.0 Safari/537.36'
            ),
            extra_http_headers={
                'Accept-Language': 'en-GB,en;q=0.9,de;q=0.8',
                'Accept': 'text/html,application/xhtml+xml',
            },
            timezone_id='Europe/Berlin',
        )

        # Anti-detection: override navigator properties
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-GB', 'en', 'de']});
            window.chrome = {runtime: {}};
        """)

        return context

    async def scrape_company(self, linkedin_url: str) -> LinkedInCompany:
        """Scrape LinkedIn company page"""
        await self._init_browser()
        context = await self._create_context()
        page = await context.new_page()

        company = LinkedInCompany(url=linkedin_url, scraper_used="playwright")

        try:
            logger.info(f"[Playwright] Scraping: {linkedin_url}")
            await page.goto(linkedin_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)

            content = await page.content()

            # Check if blocked/login wall
            if 'authwall' in content.lower() or 'sign in' in content.lower()[:2000]:
                logger.warning("[Playwright] LinkedIn auth wall detected")
                # Still try to extract from public HTML
                pass

            # Extract company name
            try:
                h1 = await page.locator('h1').first.text_content()
                company.name = h1.strip() if h1 else ""
            except:
                pass

            # Extract from meta tags (works even without login)
            try:
                desc_meta = await page.locator('meta[name="description"]').first.get_attribute('content')
                if desc_meta:
                    company.description = desc_meta
            except:
                pass

            # Extract from JSON-LD if available
            try:
                json_ld_script = await page.evaluate("""
                    () => {
                        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                        for (const s of scripts) {
                            try {
                                const data = JSON.parse(s.textContent);
                                if (data['@type'] === 'Organization' || data['@type'] === 'Corporation') {
                                    return JSON.stringify(data);
                                }
                            } catch {}
                        }
                        return null;
                    }
                """)
                if json_ld_script:
                    ld_data = json.loads(json_ld_script)
                    company.name = company.name or ld_data.get('name', '')
                    company.website = ld_data.get('url', '')
                    if 'address' in ld_data:
                        addr = ld_data['address']
                        if isinstance(addr, dict):
                            company.location = addr.get('addressLocality', '')
                            company.country = addr.get('addressCountry', '')
            except:
                pass

            # Extract full page text for AI analysis
            plain_text = await page.evaluate("""
                () => document.body.innerText.substring(0, 8000)
            """)
            if plain_text and not company.description:
                company.description = plain_text[:2000]

            # Try to find industry, size from page text
            company.industry = self._extract_field(plain_text, ["industry", "branche"])
            company.size = self._extract_field(plain_text, ["company size", "employees", "mitarbeiter"])
            if not company.country:
                company.country = self._extract_field(plain_text, ["headquarters", "hauptsitz"])

            logger.info(f"[Playwright] Got: {company.name} ({company.industry})")
            return company

        finally:
            await context.close()

    async def scrape_about_page(self, linkedin_url: str) -> str:
        """Scrape the /about page for more company details"""
        about_url = linkedin_url.rstrip('/') + '/about/'
        await self._init_browser()
        context = await self._create_context()
        page = await context.new_page()

        try:
            await page.goto(about_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(2000)
            text = await page.evaluate("() => document.body.innerText.substring(0, 8000)")
            return text or ""
        except:
            return ""
        finally:
            await context.close()

    def _extract_field(self, text: str, keywords: List[str]) -> str:
        """Extract a field value that appears after a keyword in text"""
        if not text:
            return ""
        for kw in keywords:
            pattern = rf'{kw}\s*[:\-]?\s*(.+?)(?:\n|$)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:200]
        return ""

    async def close(self):
        """Cleanup browser resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


# ============================================================================
# STRATEGY 2: SCRAPERAPI (residential proxies)
# ============================================================================

class ScraperAPILinkedIn:
    """
    Scrape LinkedIn via ScraperAPI residential proxies.

    Reuses pattern from allegro_scraper_with_scraperapi.py:
    - EU residential IPs
    - JavaScript rendering
    - Auto retry + CAPTCHA solving
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SCRAPERAPI_KEY')
        if not self.api_key:
            raise ValueError(
                "ScraperAPI key required!\n"
                "1. Sign up: https://www.scraperapi.com/signup (FREE trial: 5K requests)\n"
                "2. Get API key from dashboard\n"
                "3. Set: export SCRAPERAPI_KEY='your_key'"
            )
        self.base_url = "http://api.scraperapi.com"

    async def scrape_company(self, linkedin_url: str) -> LinkedInCompany:
        """Scrape LinkedIn company page via ScraperAPI"""
        company = LinkedInCompany(url=linkedin_url, scraper_used="scraperapi")

        params = {
            'api_key': self.api_key,
            'url': linkedin_url,
            'country_code': 'de',  # German residential IP (EU target)
            'render': 'true',
        }
        url = f"{self.base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status != 200:
                        raise Exception(f"ScraperAPI returned {response.status}")

                    html = await response.text()
                    company = self._parse_linkedin_html(html, linkedin_url)
                    company.scraper_used = "scraperapi"
                    logger.info(f"[ScraperAPI] Got: {company.name}")
                    return company

        except Exception as e:
            logger.error(f"[ScraperAPI] Failed: {e}")
            raise

    def _parse_linkedin_html(self, html: str, url: str) -> LinkedInCompany:
        """Parse LinkedIn HTML with BeautifulSoup"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')
        company = LinkedInCompany(url=url)

        # Company name from h1 or og:title
        h1 = soup.find('h1')
        if h1:
            company.name = h1.get_text(strip=True)

        og_title = soup.find('meta', property='og:title')
        if og_title and not company.name:
            company.name = og_title.get('content', '').split('|')[0].strip()

        # Description from meta
        desc = soup.find('meta', attrs={'name': 'description'})
        if desc:
            company.description = desc.get('content', '')

        # JSON-LD structured data
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if data.get('@type') in ['Organization', 'Corporation']:
                    company.name = company.name or data.get('name', '')
                    company.website = data.get('url', '')
                    if 'address' in data:
                        addr = data['address']
                        if isinstance(addr, dict):
                            company.location = addr.get('addressLocality', '')
                            company.country = addr.get('addressCountry', '')
            except:
                continue

        # Plain text for field extraction
        text = soup.get_text(separator='\n', strip=True)[:5000]
        if not company.industry:
            for line in text.split('\n'):
                if 'industry' in line.lower() or 'branche' in line.lower():
                    company.industry = line.strip()[:200]
                    break

        return company


# ============================================================================
# STRATEGY 3: DIRECT HTTP (fast but may be blocked)
# ============================================================================

class DirectHTTPLinkedIn:
    """Simple HTTP GET - works for public company pages sometimes"""

    async def scrape_company(self, linkedin_url: str) -> LinkedInCompany:
        """Direct HTTP scrape - fastest but least reliable"""
        company = LinkedInCompany(url=linkedin_url, scraper_used="direct_http")

        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml',
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    linkedin_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                    allow_redirects=True
                ) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")

                    html = await response.text()

                    # Quick check: did we get real content or auth wall?
                    if 'authwall' in html.lower() or len(html) < 5000:
                        raise Exception("Auth wall or empty response")

                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')

                    # Extract basics from meta tags
                    og_title = soup.find('meta', property='og:title')
                    if og_title:
                        company.name = og_title.get('content', '').split('|')[0].strip()

                    desc = soup.find('meta', attrs={'name': 'description'})
                    if desc:
                        company.description = desc.get('content', '')

                    logger.info(f"[Direct] Got: {company.name}")
                    return company

        except Exception as e:
            logger.warning(f"[Direct] Failed: {e}")
            raise


# ============================================================================
# MAIN SCRAPER (orchestrates all strategies with failover)
# ============================================================================

class PyroxLinkedInScraper:
    """
    Main scraper with automatic failover between strategies.

    Order:
    1. Direct HTTP (free, fast) - try first
    2. Playwright (free, slower, anti-detection) - if direct fails
    3. ScraperAPI (paid, most reliable) - last resort

    Usage:
        scraper = PyroxLinkedInScraper()
        leads = await scraper.scrape_company_leads("https://linkedin.com/company/freshfields")
        for lead in leads:
            payload = lead.to_webhook_payload()
            # POST to http://localhost:5678/webhook/ai-sales-agent
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
        # Need at least name + one of: industry, location/country, or size
        if not company.name:
            return False
        has_industry = bool(company.industry)
        has_location = bool(company.country or company.location)
        has_size = bool(company.size)
        return has_industry or has_location or has_size

    async def scrape_company(self, linkedin_url: str) -> LinkedInCompany:
        """
        Scrape company with automatic failover.

        Tries: Direct → Playwright → ScraperAPI
        Falls through if data is too thin for reliable scoring.
        """
        errors = []

        # Strategy 1: Direct HTTP (free, fast)
        try:
            direct = DirectHTTPLinkedIn()
            company = await direct.scrape_company(linkedin_url)
            if self._has_enough_data(company):
                return company
            logger.info(f"Direct got name only, escalating to Playwright...")
        except Exception as e:
            errors.append(f"Direct: {e}")
            logger.info(f"Direct failed, trying Playwright...")

        # Strategy 2: Playwright (free, anti-detection)
        if self.use_playwright:
            try:
                if not self._playwright_scraper:
                    self._playwright_scraper = PlaywrightLinkedInScraper(headless=self.headless)
                company = await self._playwright_scraper.scrape_company(linkedin_url)
                if self._has_enough_data(company):
                    return company
                logger.info(f"Playwright got thin data, trying ScraperAPI...")
            except Exception as e:
                errors.append(f"Playwright: {e}")
                logger.info(f"Playwright failed, trying ScraperAPI...")

        # Strategy 3: ScraperAPI (paid, most reliable)
        if self.use_scraperapi:
            try:
                scraper_api = ScraperAPILinkedIn(api_key=self.scraperapi_key)
                company = await scraper_api.scrape_company(linkedin_url)
                if company.name:
                    return company
            except Exception as e:
                errors.append(f"ScraperAPI: {e}")

        # All strategies failed
        logger.error(f"All scraping strategies failed for {linkedin_url}: {errors}")
        return LinkedInCompany(
            url=linkedin_url,
            description=f"Scraping failed: {'; '.join(errors)}",
            scraper_used="none"
        )

    async def scrape_company_leads(
        self,
        linkedin_url: str,
        min_score: int = 4,
    ) -> List[PyroxLead]:
        """
        Full pipeline: scrape company → qualify → find decision makers → build leads.

        Args:
            linkedin_url: LinkedIn company URL
            min_score: Minimum Pyrox score to continue (default 4)

        Returns:
            List of PyroxLead objects ready for Sales Agent webhook
        """
        now = datetime.now().isoformat()

        # Step 1: Scrape company
        logger.info(f"Step 1: Scraping company {linkedin_url}")
        company = await self.scrape_company(linkedin_url)

        # Step 2: Qualify
        score = calculate_pyrox_score(company)
        logger.info(f"Step 2: Pyrox score = {score}/10 for {company.name}")

        if score < min_score:
            logger.info(f"Score {score} < {min_score}, skipping {company.name}")
            return []

        # Step 3: Build leads from company info
        # NOTE: Employee scraping requires Apify (external service)
        # This scraper focuses on company-level intelligence
        # The n8n workflow handles employee scraping via Apify
        leads = [
            PyroxLead(
                name=f"Decision Maker at {company.name}",
                email="",  # Found by AnyMailFinder in n8n
                company=company.name,
                website=company.website,
                designation="",  # Set by n8n Groq filter
                linkedin_url=linkedin_url,
                industry=company.industry,
                country=company.country or company.location,
                pyrox_score=score,
                best_approach=self._determine_approach(company, score),
                scraped_at=now,
            )
        ]

        return leads

    async def scrape_multiple(
        self,
        urls: List[str],
        delay: float = 3.0,
        min_score: int = 4,
    ) -> List[PyroxLead]:
        """
        Scrape multiple companies with rate limiting.

        Args:
            urls: List of LinkedIn company URLs
            delay: Seconds between requests (avoid rate limiting)
            min_score: Minimum Pyrox score

        Returns:
            All qualified leads across all companies
        """
        all_leads = []

        for i, url in enumerate(urls, 1):
            logger.info(f"\n[{i}/{len(urls)}] {url}")

            try:
                leads = await self.scrape_company_leads(url, min_score=min_score)
                all_leads.extend(leads)
                logger.info(f"  Found {len(leads)} leads (score >= {min_score})")
            except Exception as e:
                logger.error(f"  Error: {e}")

            # Rate limiting between requests
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
        """
        Send leads to n8n Sales Agent webhook.

        Args:
            leads: List of PyroxLead objects
            webhook_url: n8n webhook URL (default: local Sales Agent)

        Returns:
            List of webhook responses
        """
        responses = []

        async with aiohttp.ClientSession() as session:
            for lead in leads:
                payload = lead.to_webhook_payload()

                try:
                    async with session.post(
                        webhook_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        result = await response.json()
                        responses.append(result)
                        logger.info(f"Sent to n8n: {lead.company} - {response.status}")
                except Exception as e:
                    logger.error(f"Failed to send {lead.company}: {e}")
                    responses.append({"error": str(e)})

                # Small delay between webhook calls
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


# ============================================================================
# LINKEDIN EMPLOYEE FINDER (replaces Apify - FREE)
# Based on linkedin_find_prospects.py from amazon-master-tool
# Uses LinkedIn people search to find decision makers at a company
# ============================================================================

# Where to store LinkedIn session cookies (persists between runs)
COOKIES_FILE = os.path.join(os.path.dirname(__file__), "linkedin_cookies.json")

# Search templates - combine with company name to find employees
# Why specific roles: LinkedIn people search works best with exact titles
EMPLOYEE_SEARCH_ROLES = [
    "CTO",
    "Chief Technology Officer",
    "CIO",
    "CISO",
    "Data Protection Officer",
    "DPO",
    "VP Technology",
    "Head of IT",
    "IT Director",
    "Managing Partner",  # Law firms
]


class LinkedInEmployeeFinder:
    """
    Find decision makers at a company using LinkedIn people search.

    Better than Apify because:
    - FREE (no API costs)
    - Real browser automation (anti-detection)
    - Searches by role+company so we get targeted results
    - Returns data in same format as Apify (name, designation, link)

    Requires one-time setup: run --setup-cookies to login and save session.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser = None

    async def _init_browser(self):
        """Initialize Playwright browser with anti-detection"""
        if self._browser:
            return

        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )

    async def _create_context(self):
        """Browser context with LinkedIn-appropriate settings"""
        context = await self._browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent=(
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/131.0.0.0 Safari/537.36'
            ),
            locale='en-US',
            timezone_id='Europe/Berlin',
        )

        # Anti-detection overrides
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            window.chrome = {runtime: {}};
        """)

        return context

    async def _login(self, page, context) -> bool:
        """Login to LinkedIn using saved cookies"""
        # Load cookies if available
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE) as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            logger.info("Loaded LinkedIn session cookies")

        await page.goto("https://www.linkedin.com/feed/")
        await asyncio.sleep(3)

        if "login" in page.url:
            logger.warning(
                "LinkedIn login required. Run: python pyrox_linkedin_scraper.py --setup-cookies"
            )
            return False

        # Refresh cookies for next time
        cookies = await context.cookies()
        with open(COOKIES_FILE, 'w') as f:
            json.dump(cookies, f)

        logger.info("LinkedIn session active")
        return True

    async def find_employees(
        self,
        company_name: str,
        max_per_role: int = 2,
    ) -> List[Dict]:
        """
        Search LinkedIn for decision makers at a specific company.

        Args:
            company_name: Company name to search for
            max_per_role: Max results per role search (default 2)

        Returns:
            List of employee dicts compatible with Apify format:
            [{"name": "...", "designation": "...", "link": "...", "company": "..."}]
        """
        await self._init_browser()
        context = await self._create_context()
        page = await context.new_page()

        try:
            if not await self._login(page, context):
                return []

            employees = []
            seen_urls = set()

            for role in EMPLOYEE_SEARCH_ROLES:
                query = f"{role} {company_name}"
                results = await self._search_people(page, query, max_results=max_per_role)

                for person in results:
                    url = person.get('link', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        person['company'] = company_name
                        employees.append(person)

                # Rate limiting between searches (avoid LinkedIn blocks)
                await asyncio.sleep(random.uniform(2, 4))

            logger.info(f"Found {len(employees)} employees at {company_name}")
            return employees

        finally:
            await context.close()

    async def _search_people(
        self, page, query: str, max_results: int = 2
    ) -> List[Dict]:
        """
        Search LinkedIn people search for a query.

        Returns list of: {name, designation, link, verified}
        Same format as Apify LinkedIn employees scraper output.
        """
        prospects = []

        search_url = (
            f"https://www.linkedin.com/search/results/people/"
            f"?keywords={query.replace(' ', '%20')}"
            f"&origin=GLOBAL_SEARCH_HEADER"
        )

        logger.info(f"Searching: {query}")
        await page.goto(search_url)
        await asyncio.sleep(random.uniform(3, 5))

        # Wait for results to load
        try:
            await page.wait_for_selector(
                '.reusable-search__result-container', timeout=10000
            )
        except Exception:
            logger.info(f"No results for: {query}")
            return prospects

        results = await page.query_selector_all('.reusable-search__result-container')

        for result in results[:max_results]:
            try:
                # Get profile link
                link_elem = await result.query_selector('a.app-aware-link')
                if not link_elem:
                    continue

                href = await link_elem.get_attribute('href')
                if not href or '/in/' not in href:
                    continue

                profile_url = href.split('?')[0]

                # Get name
                name_elem = await result.query_selector('span[aria-hidden="true"]')
                name = await name_elem.inner_text() if name_elem else ""

                # Skip private profiles
                if not name or "LinkedIn Member" in name:
                    continue

                # Get headline (becomes designation)
                headline_elem = await result.query_selector(
                    '.entity-result__primary-subtitle'
                )
                headline = await headline_elem.inner_text() if headline_elem else ""

                prospects.append({
                    "name": name.strip(),
                    "designation": headline.strip()[:100],
                    "link": profile_url,
                    "verified": "",
                })

                logger.info(f"  Found: {name.strip()[:30]} - {headline.strip()[:40]}")

            except Exception:
                continue

        return prospects

    async def setup_cookies_interactive(self):
        """
        One-time setup: open browser for manual LinkedIn login.
        Opens non-headless browser, user logs in manually (incl. 2FA),
        then cookies are saved for future headless use.
        """
        from playwright.async_api import async_playwright

        print("=" * 60)
        print("LINKEDIN COOKIE SETUP")
        print("=" * 60)
        print("A browser will open. Please:")
        print("1. Log in to LinkedIn")
        print("2. Complete 2FA if prompted")
        print("3. Wait until you see your feed")
        print("4. The browser will close automatically")
        print("=" * 60)

        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent=(
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/131.0.0.0 Safari/537.36'
            ),
        )
        page = await context.new_page()

        # Load existing cookies if any
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE) as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)

        await page.goto("https://www.linkedin.com/login")
        await asyncio.sleep(2)

        # Wait for user to complete login (max 5 minutes)
        print("\nWaiting for login... (max 5 minutes)")
        try:
            await page.wait_for_url("**/feed/**", timeout=300000)
            print("Login detected!")
        except Exception:
            # Check if logged in anyway
            if "feed" not in page.url:
                print("Login timeout. Try again.")
                await browser.close()
                await pw.stop()
                return

        await asyncio.sleep(2)

        # Save cookies
        cookies = await context.cookies()
        with open(COOKIES_FILE, 'w') as f:
            json.dump(cookies, f)

        print(f"\nCookies saved to: {COOKIES_FILE}")
        print(f"Total cookies: {len(cookies)}")
        print("You can now run the scraper in headless mode.")

        await browser.close()
        await pw.stop()

    async def close(self):
        """Cleanup"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


# ============================================================================
# WEBHOOK SERVER (standalone mode - receives URLs, returns leads)
# ============================================================================

async def run_webhook_server(host: str = "0.0.0.0", port: int = 8765):
    """
    Run standalone webhook server for n8n integration.

    n8n HTTP Request node can POST to this server:
    POST http://localhost:8765/scrape
    {"linkedin_url": "https://linkedin.com/company/example"}

    Returns:
    {"company": {...}, "score": 7, "leads": [...]}
    """
    from aiohttp import web

    scraper = PyroxLinkedInScraper()
    employee_finder = LinkedInEmployeeFinder(headless=True)

    async def handle_scrape(request):
        try:
            data = await request.json()
            url = data.get('linkedin_url', '')

            if not url:
                return web.json_response({"error": "linkedin_url required"}, status=400)

            company = await scraper.scrape_company(url)
            score = calculate_pyrox_score(company)
            leads = await scraper.scrape_company_leads(url)

            return web.json_response({
                "company": asdict(company),
                "score": score,
                "leads": [asdict(l) for l in leads],
                "qualified": score >= 4,
            })

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def handle_scrape_employees(request):
        """
        Find decision makers at a company using LinkedIn people search.
        Replaces Apify LinkedIn employees scraper.

        POST /scrape-employees
        {"company_name": "Freshfields", "linkedin_url": "https://..."}

        Returns array of employees (same format as Apify):
        [{"name": "...", "designation": "...", "link": "...", "company": "..."}]
        """
        try:
            data = await request.json()
            company_name = data.get('company_name', '')

            if not company_name:
                return web.json_response(
                    {"error": "company_name required"}, status=400
                )

            # Check if cookies exist (required for LinkedIn login)
            if not os.path.exists(COOKIES_FILE):
                return web.json_response({
                    "error": "LinkedIn cookies not configured. "
                             "Run: python pyrox_linkedin_scraper.py --setup-cookies"
                }, status=503)

            employees = await employee_finder.find_employees(company_name)

            return web.json_response(employees)

        except Exception as e:
            logger.error(f"Employee scrape error: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def handle_health(request):
        has_cookies = os.path.exists(COOKIES_FILE)
        return web.json_response({
            "status": "ok",
            "service": "pyrox-linkedin-scraper",
            "linkedin_cookies": has_cookies,
        })

    app = web.Application()
    app.router.add_post('/scrape', handle_scrape)
    app.router.add_post('/scrape-employees', handle_scrape_employees)
    app.router.add_get('/health', handle_health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    logger.info(f"PYROX LinkedIn Scraper running on http://{host}:{port}")
    logger.info(f"  POST /scrape            - Scrape a LinkedIn company")
    logger.info(f"  POST /scrape-employees  - Find decision makers (replaces Apify)")
    logger.info(f"  GET  /health            - Health check")
    logger.info(f"  LinkedIn cookies: {'READY' if os.path.exists(COOKIES_FILE) else 'NOT SET (run --setup-cookies)'}")

    # Keep running
    await asyncio.Event().wait()


# ============================================================================
# CLI
# ============================================================================

async def main():
    """CLI entry point for testing"""
    import sys

    if len(sys.argv) < 2:
        print("PYROX LinkedIn Scraper")
        print()
        print("Usage:")
        print("  python pyrox_linkedin_scraper.py <linkedin_company_url>")
        print("  python pyrox_linkedin_scraper.py --server          (start webhook server)")
        print("  python pyrox_linkedin_scraper.py --batch urls.txt  (batch scrape)")
        print("  python pyrox_linkedin_scraper.py --setup-cookies   (LinkedIn login)")
        print("  python pyrox_linkedin_scraper.py --find-employees 'Company Name'")
        print()
        print("Examples:")
        print("  python pyrox_linkedin_scraper.py https://linkedin.com/company/freshfields")
        print("  python pyrox_linkedin_scraper.py --find-employees 'Freshfields'")
        print()
        print("Environment variables:")
        print("  SCRAPERAPI_KEY  - ScraperAPI key (optional, for fallback)")
        sys.exit(1)

    arg = sys.argv[1]

    # Cookie setup mode - one-time manual LinkedIn login
    if arg == '--setup-cookies':
        finder = LinkedInEmployeeFinder(headless=False)
        await finder.setup_cookies_interactive()
        return

    # Employee finder mode - search for decision makers
    if arg == '--find-employees' and len(sys.argv) > 2:
        company_name = sys.argv[2]
        finder = LinkedInEmployeeFinder(headless=True)
        try:
            employees = await finder.find_employees(company_name)
            print(f"\nFound {len(employees)} decision makers at {company_name}:")
            for emp in employees:
                priority = match_decision_maker_role(emp.get('designation', ''))
                marker = f" [P{priority}]" if priority else ""
                print(f"  {emp['name']} - {emp['designation']}{marker}")
                print(f"    {emp['link']}")
        finally:
            await finder.close()
        return

    # Server mode
    if arg == '--server':
        await run_webhook_server()
        return

    # Batch mode
    if arg == '--batch' and len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            urls = [line.strip() for line in f if line.strip()]

        scraper = PyroxLinkedInScraper()
        try:
            leads = await scraper.scrape_multiple(urls)
            print(f"\nResults: {json.dumps([asdict(l) for l in leads], indent=2)}")
        finally:
            await scraper.close()
        return

    # Single URL mode
    url = arg
    scraper = PyroxLinkedInScraper()

    try:
        print(f"Scraping: {url}")
        company = await scraper.scrape_company(url)
        score = calculate_pyrox_score(company)

        print(f"\nCompany: {company.name}")
        print(f"Website: {company.website}")
        print(f"Industry: {company.industry}")
        print(f"Location: {company.location}, {company.country}")
        print(f"Size: {company.size}")
        print(f"Scraper: {company.scraper_used}")
        print(f"Pyrox Score: {score}/10")
        print(f"Qualified: {'YES' if score >= 4 else 'NO'}")

        if score >= 4:
            leads = await scraper.scrape_company_leads(url)
            print(f"Leads: {len(leads)}")
            for lead in leads:
                print(f"  - {lead.name} | {lead.best_approach}")

    finally:
        await scraper.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.run(main())
