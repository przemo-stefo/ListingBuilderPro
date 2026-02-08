# backend/services/scraper/pyrox_linkedin/server.py
# Purpose: Standalone webhook server for n8n integration (4 endpoints + health)
# NOT for: Scraping logic — see orchestrator.py, employee_finder.py

import asyncio
import logging
import os
from dataclasses import asdict

from .models import LinkedInCompany
from .qualification import calculate_pyrox_score
from .orchestrator import PyroxLinkedInScraper
from .employee_finder import LinkedInEmployeeFinder, COOKIES_FILE
from .playwright_scraper import PlaywrightLinkedInScraper

logger = logging.getLogger(__name__)


async def run_webhook_server(host: str = "0.0.0.0", port: int = 8765):
    """
    Run standalone webhook server for n8n integration.

    POST /scrape            - Full pipeline: company + leads
    POST /scrape-company    - Company data only (fast)
    POST /scrape-profile    - Personal profile (replaces Apify)
    POST /scrape-employees  - Find decision makers
    GET  /health            - Health check
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
        """Find decision makers at a company using LinkedIn people search."""
        try:
            data = await request.json()
            company_name = data.get('company_name', '')
            if not company_name:
                return web.json_response({"error": "company_name required"}, status=400)

            has_cookies = os.path.exists(COOKIES_FILE) or bool(os.environ.get('LINKEDIN_LI_AT'))
            if not has_cookies:
                return web.json_response({
                    "error": "LinkedIn cookies not configured. "
                             "Set LINKEDIN_LI_AT env or run --setup-cookies"
                }, status=503)

            employees = await employee_finder.find_employees(company_name)
            return web.json_response(employees)
        except Exception as e:
            logger.error(f"Employee scrape error: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def handle_scrape_profile(request):
        """Scrape personal LinkedIn profile using Voyager API."""
        try:
            data = await request.json()
            url = data.get('linkedin_url', '')
            if not url:
                return web.json_response({"error": "linkedin_url required"}, status=400)

            pw_scraper = PlaywrightLinkedInScraper(headless=True)
            profile = await pw_scraper.scrape_profile(url)
            return web.json_response(profile)
        except Exception as e:
            logger.error(f"Profile scrape error: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def handle_scrape_company(request):
        """Lightweight company scrape - structured data only, no employee search."""
        try:
            data = await request.json()
            url = data.get('linkedin_url', '')
            if not url:
                return web.json_response({"error": "linkedin_url required"}, status=400)

            company = await scraper.scrape_company(url)
            score = calculate_pyrox_score(company)
            return web.json_response({"company": asdict(company), "score": score})
        except Exception as e:
            logger.error(f"Company scrape error: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def handle_health(request):
        has_cookies = os.path.exists(COOKIES_FILE) or bool(os.environ.get('LINKEDIN_LI_AT'))
        return web.json_response({
            "status": "ok",
            "service": "pyrox-linkedin-scraper",
            "linkedin_cookies": has_cookies,
        })

    app = web.Application()
    app.router.add_post('/scrape', handle_scrape)
    app.router.add_post('/scrape-profile', handle_scrape_profile)
    app.router.add_post('/scrape-company', handle_scrape_company)
    app.router.add_post('/scrape-employees', handle_scrape_employees)
    app.router.add_get('/health', handle_health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    logger.info(f"PYROX LinkedIn Scraper running on http://{host}:{port}")
    logger.info(f"  POST /scrape            - Full pipeline: company + leads")
    logger.info(f"  POST /scrape-company    - Company data only (fast)")
    logger.info(f"  POST /scrape-profile    - Personal profile (replaces Apify)")
    logger.info(f"  POST /scrape-employees  - Find decision makers")
    logger.info(f"  GET  /health            - Health check")
    logger.info(f"  LinkedIn cookies: {'READY' if os.path.exists(COOKIES_FILE) else 'NOT SET (run --setup-cookies)'}")

    await asyncio.Event().wait()
