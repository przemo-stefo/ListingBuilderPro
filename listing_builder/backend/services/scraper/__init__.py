# backend/services/scraper/__init__.py
# Purpose: Marketplace product data scraper package
# NOT for: Data conversion or template generation

import os


def get_scrape_do_token() -> str:
    """Get Scrape.do API token from env or config.

    WHY shared: Used by Rozetka, AliExpress, Temu scrapers — avoids 3x duplication.
    """
    token = os.environ.get("SCRAPE_DO_TOKEN", "")
    if not token:
        try:
            from config import settings
            token = getattr(settings, "scrape_do_token", "")
        except Exception:
            pass
    return token
