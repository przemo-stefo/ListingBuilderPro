# backend/services/scraper/pyrox_linkedin/employee_finder.py
# Purpose: Find decision makers at companies using LinkedIn people search
# NOT for: Company scraping — see orchestrator.py, strategies.py

import asyncio
import json
import logging
import os
import random
import re
from typing import List, Dict

logger = logging.getLogger(__name__)

# Where LinkedIn session cookies are stored (persists between runs)
COOKIES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "linkedin_cookies.json"
)

# Search templates - combine with company name to find employees
# WHY specific roles: LinkedIn people search works best with exact titles
EMPLOYEE_SEARCH_ROLES = [
    "CTO", "Chief Technology Officer", "CIO", "CISO",
    "Data Protection Officer", "DPO", "VP Technology",
    "Head of IT", "IT Director", "Managing Partner",
]


class LinkedInEmployeeFinder:
    """
    Find decision makers at a company using LinkedIn people search.

    Better than Apify because:
    - FREE (no API costs)
    - Real browser automation (anti-detection)
    - Searches by role+company so we get targeted results

    Safety measures:
    - Conservative daily search limit (max 30 searches/day)
    - Human-like delays (5-15s between searches)
    - Random scrolling before parsing results
    - Checkpoint/2FA detection during searches

    Requires one-time setup: run --setup-cookies to login and save session.
    """

    DAILY_SEARCH_LIMIT = 30
    MAX_ROLES_PER_COMPANY = 5

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._searches_today = 0
        self._search_date = None

    def _check_daily_limit(self) -> bool:
        """Check if we've exceeded daily search limit (safety)"""
        from datetime import date
        today = date.today()
        if self._search_date != today:
            self._search_date = today
            self._searches_today = 0
        return self._searches_today < self.DAILY_SEARCH_LIMIT

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
                '--disable-infobars',
                '--window-size=1280,900',
            ]
        )

    async def _create_context(self):
        """Browser context with LinkedIn-appropriate settings"""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        ]

        context = await self._browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent=random.choice(user_agents),
            locale='en-US',
            timezone_id='Europe/Berlin',
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'de']});
            window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}};
            delete window.__playwright;
            delete window.__pw_manual;
        """)

        return context

    async def _human_scroll(self, page):
        """Simulate human-like scrolling (safety measure)"""
        for _ in range(random.randint(2, 4)):
            await page.evaluate(f"window.scrollBy(0, {random.randint(200, 400)})")
            await asyncio.sleep(random.uniform(0.5, 1.5))
        await asyncio.sleep(random.uniform(1, 2))

    async def _check_session_health(self, page) -> bool:
        """Detect if LinkedIn challenged us (checkpoint, login, captcha)"""
        url = page.url
        if any(x in url for x in ['login', 'checkpoint', 'challenge', 'captcha']):
            logger.warning(f"LinkedIn session issue detected: {url}")
            return False
        return True

    async def _login(self, page, context) -> bool:
        """Login to LinkedIn using saved cookies or env variable"""
        cookies_loaded = False

        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE) as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            cookies_loaded = True
            logger.info("Loaded LinkedIn cookies from file")

        if not cookies_loaded:
            li_at = os.environ.get('LINKEDIN_LI_AT', '')
            if li_at:
                await context.add_cookies([{
                    "name": "li_at",
                    "value": li_at,
                    "domain": ".linkedin.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True,
                    "sameSite": "None",
                }])
                cookies_loaded = True
                logger.info("Loaded LinkedIn cookie from LINKEDIN_LI_AT env")

        await page.goto("https://www.linkedin.com/feed/")
        await asyncio.sleep(3)

        if "login" in page.url:
            if not cookies_loaded:
                logger.warning(
                    "LinkedIn login required. Set LINKEDIN_LI_AT env or run --setup-cookies"
                )
            else:
                logger.warning("LinkedIn cookies expired. Get fresh li_at cookie.")
            return False

        # Refresh cookies for next time
        cookies = await context.cookies()
        with open(COOKIES_FILE, 'w') as f:
            json.dump(cookies, f)

        logger.info("LinkedIn session active")
        return True

    async def find_employees(
        self, company_name: str, max_per_role: int = 2,
    ) -> List[Dict]:
        """
        Search LinkedIn for decision makers at a specific company.

        Safety: respects daily limit, human-like delays (5-15s),
        session health monitoring, stops early if enough found.
        """
        if not self._check_daily_limit():
            logger.warning(
                f"Daily search limit reached ({self.DAILY_SEARCH_LIMIT}). "
                "Try again tomorrow to keep LinkedIn account safe."
            )
            return []

        await self._init_browser()
        context = await self._create_context()
        page = await context.new_page()

        try:
            if not await self._login(page, context):
                return []

            employees = []
            seen_urls = set()
            roles_to_search = EMPLOYEE_SEARCH_ROLES[:self.MAX_ROLES_PER_COMPANY]

            for i, role in enumerate(roles_to_search):
                if not self._check_daily_limit():
                    logger.warning("Daily limit hit mid-search, stopping early.")
                    break

                if not await self._check_session_health(page):
                    logger.warning("Session compromised, stopping search.")
                    break

                query = f"{role} {company_name}"
                results = await self._search_people(page, query, max_results=max_per_role)
                self._searches_today += 1

                for person in results:
                    url = person.get('link', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        person['company'] = company_name
                        person['designation'] = self._clean_designation(
                            person.get('designation', ''), company_name
                        )
                        employees.append(person)

                if len(employees) >= 5:
                    logger.info(f"Found {len(employees)} employees, stopping early.")
                    break

                # Safety: human-like delay between searches (5-15s)
                if i < len(roles_to_search) - 1:
                    delay = random.uniform(5, 15)
                    logger.info(f"  Safety delay: {delay:.1f}s before next search")
                    await asyncio.sleep(delay)

            logger.info(
                f"Found {len(employees)} employees at {company_name} "
                f"(searches today: {self._searches_today}/{self.DAILY_SEARCH_LIMIT})"
            )
            return employees

        finally:
            await context.close()

    def _clean_designation(self, desig: str, company_name: str) -> str:
        """
        Strip location glued after company name in designation.
        WHY: LinkedIn renders title+location in separate divs but
        textContent concatenates them (e.g. "CTO @ FreshfieldsNew York")
        """
        lower = desig.lower()
        cn_lower = company_name.lower()
        idx = lower.rfind(cn_lower)
        if idx >= 0:
            return desig[:idx + len(cn_lower)].strip()

        # Fallback: find glue point where lowercase meets uppercase with no space
        # WHY: LinkedIn renders separate divs that concatenate
        m = re.search(r'([a-z])([A-Z])', desig)
        if m and m.start() > 4:
            return desig[:m.start() + 1].strip()

        return desig

    async def _search_people(
        self, page, query: str, max_results: int = 2
    ) -> List[Dict]:
        """
        Search LinkedIn people search for a query.

        Uses JavaScript DOM extraction instead of CSS selectors because
        LinkedIn frequently changes their class names.
        """
        from urllib.parse import quote

        search_url = (
            f"https://www.linkedin.com/search/results/people/"
            f"?keywords={quote(query)}"
            f"&origin=GLOBAL_SEARCH_HEADER"
        )

        logger.info(f"Searching: {query}")
        await page.goto(search_url, wait_until='domcontentloaded')
        await asyncio.sleep(random.uniform(4, 7))

        if not await self._check_session_health(page):
            logger.warning("Session lost during search, aborting.")
            return []

        await self._human_scroll(page)

        # WHY JS: LinkedIn changes class names often. Finding all <a> tags
        # with /in/ hrefs and extracting nearby text is more stable.
        prospects = await page.evaluate(f"""
            (() => {{
                const results = [];
                const links = document.querySelectorAll('a[href*="/in/"]');
                const seen = new Set();

                for (const link of links) {{
                    const href = link.href.split('?')[0];
                    if (!href || seen.has(href)) continue;
                    if (href.includes('/search/') || href.includes('/feed/')) continue;

                    let name = '';
                    const nameSpan = link.querySelector('span[aria-hidden="true"]');
                    if (nameSpan) {{
                        name = nameSpan.textContent.trim();
                    }} else {{
                        name = link.textContent.trim().split('\\n')[0].trim();
                    }}

                    if (!name || name.includes('LinkedIn Member') || name.length < 2) continue;
                    if (name.length > 60) continue;

                    let headline = '';
                    let container = link.closest('li') || link.parentElement?.parentElement?.parentElement;
                    if (container) {{
                        const subtitleEl = container.querySelector(
                            '.entity-result__primary-subtitle, ' +
                            '[class*="subtitle"], ' +
                            '[class*="headline"]'
                        );
                        if (subtitleEl) {{
                            headline = subtitleEl.textContent.trim();
                        }} else {{
                            const allText = container.textContent;
                            const nameIdx = allText.indexOf(name);
                            if (nameIdx >= 0) {{
                                const after = allText.substring(nameIdx + name.length).trim();
                                const firstLine = after.split('\\n').map(s => s.trim()).filter(s => s.length > 5)[0] || '';
                                if (firstLine.length < 120) headline = firstLine;
                            }}
                        }}
                    }}

                    headline = headline
                        .replace(/^[\\s•·\\-]+/, '')
                        .replace(/^\\d+(st|nd|rd|th)\\+?/i, '')
                        .replace(/Message$/i, '')
                        .replace(/Connect$/i, '')
                        .replace(/Follow$/i, '')
                        .trim();

                    seen.add(href);
                    results.push({{
                        name: name,
                        designation: headline.substring(0, 100),
                        link: href,
                        verified: ''
                    }});

                    if (results.length >= {max_results}) break;
                }}

                return results;
            }})()
        """)

        if not prospects:
            debug_path = os.path.join(os.path.dirname(__file__), "debug_search.png")
            try:
                await page.screenshot(path=debug_path)
                logger.info(f"  Debug screenshot saved: {debug_path}")
            except Exception:
                pass
            logger.info(f"No results for: {query}")
        else:
            for p in prospects:
                logger.info(f"  Found: {p['name'][:30]} - {p['designation'][:40]}")

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

        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE) as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)

        await page.goto("https://www.linkedin.com/login")
        await asyncio.sleep(2)

        print("\nWaiting for login... (max 5 minutes)")
        try:
            await page.wait_for_url("**/feed/**", timeout=300000)
            print("Login detected!")
        except Exception:
            if "feed" not in page.url:
                print("Login timeout. Try again.")
                await browser.close()
                await pw.stop()
                return

        await asyncio.sleep(2)

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
