# backend/services/scraper/pyrox_linkedin/cli.py
# Purpose: CLI entry point for testing and standalone usage
# NOT for: Library usage — import from __init__.py instead

import asyncio
import json
import logging
import sys
from dataclasses import asdict

from .models import PyroxLead
from .qualification import match_decision_maker_role, calculate_pyrox_score
from .orchestrator import PyroxLinkedInScraper
from .employee_finder import LinkedInEmployeeFinder
from .server import run_webhook_server


async def main():
    """CLI entry point for testing"""
    if len(sys.argv) < 2:
        print("PYROX LinkedIn Scraper")
        print()
        print("Usage:")
        print("  python -m backend.services.scraper.pyrox_linkedin.cli <linkedin_company_url>")
        print("  python -m backend.services.scraper.pyrox_linkedin.cli --server")
        print("  python -m backend.services.scraper.pyrox_linkedin.cli --batch urls.txt")
        print("  python -m backend.services.scraper.pyrox_linkedin.cli --setup-cookies")
        print("  python -m backend.services.scraper.pyrox_linkedin.cli --find-employees 'Company'")
        print()
        print("Examples:")
        print("  python -m backend.services.scraper.pyrox_linkedin.cli https://linkedin.com/company/freshfields")
        print("  python -m backend.services.scraper.pyrox_linkedin.cli --find-employees 'Freshfields'")
        print()
        print("Environment variables:")
        print("  SCRAPERAPI_KEY  - ScraperAPI key (optional, for fallback)")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == '--setup-cookies':
        finder = LinkedInEmployeeFinder(headless=False)
        await finder.setup_cookies_interactive()
        return

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

    if arg == '--server':
        await run_webhook_server()
        return

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
