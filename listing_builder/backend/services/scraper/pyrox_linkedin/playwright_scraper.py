# backend/services/scraper/pyrox_linkedin/playwright_scraper.py
# Purpose: Playwright browser + Voyager API scraping strategy
# NOT for: Direct HTTP or ScraperAPI — see strategies.py

import json
import logging
import os
import re
from typing import List, Dict

from .models import LinkedInCompany

logger = logging.getLogger(__name__)

# Where LinkedIn session cookies are stored (shared with employee_finder)
COOKIES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "linkedin_cookies.json"
)


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
                pass

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

            # Extract full page text for field extraction
            plain_text = await page.evaluate(
                "() => document.body.innerText.substring(0, 8000)"
            )
            if plain_text and not company.description:
                company.description = plain_text[:2000]

            company.industry = self._extract_field(plain_text, ["industry", "branche"])
            company.size = self._extract_field(plain_text, ["company size", "employees", "mitarbeiter"])
            if not company.country:
                company.country = self._extract_field(plain_text, ["headquarters", "hauptsitz"])

            logger.info(f"[Playwright] Got: {company.name} ({company.industry})")
            return company

        finally:
            await context.close()

    async def scrape_profile(self, profile_url: str) -> Dict:
        """
        Scrape personal LinkedIn profile via Voyager API.
        Returns structured data for n8n personalization workflow.

        Uses LinkedIn's internal API (same as the web app) for reliable data.
        Requires linkedin_cookies.json or LINKEDIN_LI_AT env var.
        """
        import urllib.request
        import urllib.error

        result = {
            "profileUrl": profile_url,
            "name": "", "headline": "", "about": "",
            "location": "", "experience": [], "recentPosts": [],
            "scraperUsed": "pyrox-voyager-api",
            "authenticated": False,
        }

        # Extract public identifier from URL
        public_id = profile_url.rstrip('/').split('/in/')[-1].split('?')[0]
        if not public_id:
            result["error"] = "Could not extract public identifier from URL"
            return result

        # Load auth cookies
        li_at = None
        jsessionid = "ajax:0000000000000000000"

        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE) as f:
                cookies = json.load(f)
            for c in cookies:
                if c['name'] == 'li_at':
                    li_at = c['value']
                elif c['name'] == 'JSESSIONID':
                    jsessionid = c['value'].strip('"')
        elif os.environ.get('LINKEDIN_LI_AT'):
            li_at = os.environ['LINKEDIN_LI_AT']

        if not li_at:
            result["error"] = (
                "No LinkedIn cookies found. "
                "Need linkedin_cookies.json or LINKEDIN_LI_AT env var."
            )
            return result

        result["authenticated"] = True
        return await self._fetch_voyager_profile(
            public_id, li_at, jsessionid, result
        )

    async def _fetch_voyager_profile(
        self, public_id: str, li_at: str, jsessionid: str, result: Dict
    ) -> Dict:
        """Fetch profile data from LinkedIn Voyager API"""
        import urllib.request
        import urllib.error

        try:
            logger.info(f"[Profile] Voyager API for: {public_id}")

            api_url = (
                "https://www.linkedin.com/voyager/api/identity/dash/profiles"
                f"?q=memberIdentity&memberIdentity={public_id}"
                "&decorationId=com.linkedin.voyager.dash.deco.identity.profile"
                ".FullProfileWithEntities-93"
            )

            headers = {
                "Cookie": f'li_at={li_at}; JSESSIONID="{jsessionid}"',
                "csrf-token": jsessionid,
                "Accept": "application/vnd.linkedin.normalized+json+2.1",
                "x-restli-protocol-version": "2.0.0",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            }

            req = urllib.request.Request(api_url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            included = data.get('included', [])

            self._extract_profile_entity(included, public_id, result)
            self._resolve_location(included, result)
            self._extract_positions(included, result)

            logger.info(
                f"[Profile] Got: {result['name']} | "
                f"headline={'yes' if result['headline'] else 'no'} | "
                f"about={'yes' if result['about'] else 'no'} | "
                f"exp={len(result['experience'])}"
            )
            return result

        except Exception as e:
            logger.error(f"[Profile] Error: {e}")
            result["error"] = str(e)
            return result

    def _extract_profile_entity(self, included, public_id, result):
        """Extract name/headline/about from Voyager profile entity"""
        for item in included:
            if item.get('$type') == 'com.linkedin.voyager.dash.identity.profile.Profile':
                fn = item.get('firstName', '')
                ln = item.get('lastName', '')
                pid = item.get('publicIdentifier', '')
                # WHY: match by publicIdentifier to avoid picking up viewer's profile
                if pid == public_id or (fn and not pid):
                    result["name"] = f"{fn} {ln}".strip()
                    result["headline"] = item.get('headline', '')
                    result["about"] = (item.get('summary', '') or '')[:3000]
                    result["location"] = item.get('locationName', '')
                    geo_urn = (item.get('geoLocation', {}) or {}).get('*geo', '')
                    if not result["location"] and geo_urn:
                        result["_geoUrn"] = geo_urn
                    break

    def _resolve_location(self, included, result):
        """Resolve location from geo entities if not in profile directly"""
        if not result["location"]:
            geo_urn = result.pop("_geoUrn", "")
            for item in included:
                if item.get('$type', '').endswith('.Geo') and item.get('entityUrn') == geo_urn:
                    result["location"] = item.get('defaultLocalizedName', '')
                    break
            if not result["location"]:
                for item in included:
                    if item.get('$type', '').endswith('.Geo'):
                        name = item.get('defaultLocalizedName', '')
                        if ',' in name:
                            result["location"] = name
                            break
        else:
            result.pop("_geoUrn", None)

    def _extract_positions(self, included, result):
        """Extract work positions from Voyager response"""
        for item in included:
            if item.get('$type') == 'com.linkedin.voyager.dash.identity.profile.Position':
                result["experience"].append({
                    "position": item.get('title', ''),
                    "company": item.get('companyName', ''),
                    "duration": "",
                    "description": (item.get('description', '') or '')[:500],
                    "location": item.get('locationName', ''),
                })
        result["experience"] = result["experience"][:5]

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
