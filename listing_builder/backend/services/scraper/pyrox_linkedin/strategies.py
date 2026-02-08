# backend/services/scraper/pyrox_linkedin/strategies.py
# Purpose: DirectHTTP and ScraperAPI scraping strategies
# NOT for: Playwright scraping — see playwright_scraper.py

import json
import logging
import os
from typing import Optional

import aiohttp

from .models import LinkedInCompany

logger = logging.getLogger(__name__)


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
