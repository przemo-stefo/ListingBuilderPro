# backend/services/audit_service.py
# Purpose: Product card audit — scrape → run checks → generate AI fix suggestions
# NOT for: Template file validation (that's compliance/service.py)

import re
import structlog
from typing import List, Dict

from config import settings
from services.scraper.allegro_scraper import scrape_allegro_product, AllegroProduct
from services.compliance.allegro_rules import validate_allegro_parameters
from services.scraper.amazon_scraper import parse_input as parse_amazon_input
from services.sp_api_catalog import fetch_catalog_item
from services.ebay_service import fetch_ebay_product

logger = structlog.get_logger()


# ── Base audit rules for scraped product cards ───────────────────────────────
# WHY separate from allegro_rules.py: These check top-level product fields
# (title, images, description). allegro_rules.py checks parameters dict deeply.

ALLEGRO_BASE_RULES = [
    {"field": "title", "check": "not_empty", "severity": "error",
     "message": "Brak tytułu produktu"},
    {"field": "title", "check": "max_length", "max": 75, "severity": "warning",
     "message": "Tytuł dłuższy niż 75 znaków — obcięty na mobile"},
    {"field": "ean", "check": "not_empty", "severity": "error",
     "message": "Brak kodu EAN/GTIN — wymagany przez Allegro"},
    {"field": "brand", "check": "not_empty", "severity": "warning",
     "message": "Brak marki — klienci filtrują po marce"},
    {"field": "images", "check": "min_count", "min": 1, "severity": "error",
     "message": "Brak zdjęć produktu"},
    {"field": "images", "check": "min_count", "min": 3, "severity": "warning",
     "message": "Mniej niż 3 zdjęcia — dodaj więcej dla lepszej konwersji"},
    {"field": "description", "check": "not_empty", "severity": "warning",
     "message": "Brak opisu produktu — wpływa na SEO i konwersję"},
    {"field": "description", "check": "min_length", "min": 100, "severity": "warning",
     "message": "Opis krótszy niż 100 znaków — zbyt krótki dla SEO"},
    {"field": "price", "check": "not_empty", "severity": "error",
     "message": "Brak ceny produktu"},
    {"field": "category", "check": "not_empty", "severity": "warning",
     "message": "Brak kategorii — produkt może nie wyświetlać się w filtrach"},
    {"field": "parameters", "check": "min_count", "min": 3, "severity": "warning",
     "message": "Mniej niż 3 parametry wypełnione — uzupełnij dla lepszej widoczności"},
    {"field": "condition", "check": "not_empty", "severity": "warning",
     "message": "Brak informacji o stanie produktu (Nowy/Używany)"},
]


# WHY: Amazon scraper returns title, bullets, description — no images/EAN/price from HTML
AMAZON_BASE_RULES = [
    {"field": "title", "check": "not_empty", "severity": "error",
     "message": "Brak tytułu produktu"},
    {"field": "title", "check": "max_length", "max": 200, "severity": "warning",
     "message": "Tytuł dłuższy niż 200 znaków — Amazon może obciąć"},
    {"field": "bullets", "check": "min_count", "min": 1, "severity": "error",
     "message": "Brak bullet pointów — Amazon wymaga minimum jednego"},
    {"field": "bullets", "check": "min_count", "min": 5, "severity": "warning",
     "message": "Mniej niż 5 bullet pointów — Amazon rekomenduje 5 dla lepszej konwersji"},
    {"field": "description", "check": "not_empty", "severity": "warning",
     "message": "Brak opisu produktu — wpływa na konwersję i A9 SEO"},
]


# WHY: eBay scraper returns title, price, condition, listing_active — no bullets/images
EBAY_BASE_RULES = [
    {"field": "title", "check": "not_empty", "severity": "error",
     "message": "Brak tytułu produktu"},
    {"field": "title", "check": "max_length", "max": 80, "severity": "warning",
     "message": "Tytuł dłuższy niż 80 znaków — limit eBay"},
    {"field": "price", "check": "not_empty", "severity": "error",
     "message": "Brak ceny produktu"},
    {"field": "listing_active", "check": "is_true", "severity": "error",
     "message": "Aukcja zakończona — oferta nie jest aktywna"},
    {"field": "condition", "check": "not_empty", "severity": "warning",
     "message": "Brak informacji o stanie produktu"},
]


def _extract_audit_fields(product: AllegroProduct) -> Dict:
    """Map AllegroProduct to flat dict for base rule evaluation."""
    return {
        "title": product.title or "",
        "ean": product.ean or "",
        "brand": product.brand or "",
        "manufacturer": product.manufacturer or "",
        "images": product.images or [],
        "description": product.description or "",
        "price": product.price or "",
        "category": product.category or "",
        "parameters": product.parameters or {},
        "condition": product.condition or "",
    }


def _run_base_rules(fields: Dict, rules: list) -> List[Dict]:
    """Run base audit rules against extracted fields."""
    issues = []
    for rule in rules:
        field_name = rule["field"]
        value = fields.get(field_name, "")
        check = rule["check"]
        violated = False

        if check == "not_empty":
            if isinstance(value, (list, dict)):
                violated = len(value) == 0
            else:
                violated = not str(value).strip()
        elif check == "max_length":
            if isinstance(value, str) and len(value) > rule["max"]:
                violated = True
        elif check == "min_length":
            if isinstance(value, str) and len(value.strip()) > 0 and len(value.strip()) < rule["min"]:
                violated = True
        elif check == "min_count":
            if isinstance(value, (list, dict)):
                violated = len(value) < rule["min"]
        elif check == "is_true":
            # WHY: eBay listing_active — False means listing ended
            violated = not value

        if violated:
            issues.append({
                "field": field_name,
                "severity": rule["severity"],
                "message": rule["message"],
            })

    return issues


async def _generate_fix_suggestions(issues: List[Dict], product_title: str) -> List[Dict]:
    """Use Groq to generate fix suggestions for each issue."""
    if not issues:
        return issues

    issues_text = "\n".join(
        f"- [{i['severity'].upper()}] Pole: {i['field']} — {i['message']}"
        for i in issues
    )

    prompt = f"""Jesteś ekspertem od compliance marketplace. Produkt: "{product_title}"

Znalezione problemy:
{issues_text}

Dla KAŻDEGO problemu podaj krótką, konkretną sugestię naprawy (1-2 zdania po polsku).
Format: po jednej linii na problem, w tej samej kolejności co powyżej.
Nie dodawaj numerów ani prefiksów — sama sugestia."""

    try:
        import httpx

        api_key = settings.groq_api_key
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 800,
                },
            )

        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            suggestions = [s.strip() for s in content.strip().split("\n") if s.strip()]

            for i, issue in enumerate(issues):
                if i < len(suggestions):
                    issue["fix_suggestion"] = suggestions[i]
                else:
                    issue["fix_suggestion"] = None
        else:
            logger.warning("audit_groq_error", status=resp.status_code)

    except Exception as e:
        logger.warning("audit_fix_suggestions_failed", error=str(e))

    return issues


def audit_product_from_data(data: Dict) -> Dict:
    """Audit a product from Allegro API data (no scraping, no AI suggestions).

    WHY separate from audit_product(): batch store scan needs speed —
    no network scrape, no LLM call. Same rules, 10x faster per product.
    """
    product = AllegroProduct(
        source_url=data.get("source_url", ""),
        source_id=data.get("source_id", ""),
        title=data.get("title", ""),
        description=data.get("description", ""),
        price=data.get("price", ""),
        currency=data.get("currency", "PLN"),
        ean=data.get("ean", ""),
        images=data.get("images", []),
        category=data.get("category", ""),
        quantity=data.get("quantity", ""),
        condition=data.get("condition", ""),
        parameters=data.get("parameters", {}),
        brand=data.get("brand", ""),
        manufacturer=data.get("manufacturer", ""),
    )

    fields = _extract_audit_fields(product)
    issues = _run_base_rules(fields, ALLEGRO_BASE_RULES)

    param_issues = validate_allegro_parameters(
        raw_params=product.parameters or {},
        title=product.title or "",
        category=product.category or "",
    )

    # WHY: Same dedup logic as audit_product — keep more specific param rule
    base_fields = {i["field"] for i in issues}
    for pi in param_issues:
        if pi["field"] not in base_fields:
            issues.append(pi)
        elif pi["severity"] == "error" and any(
            i["field"] == pi["field"] and i["severity"] != "error" for i in issues
        ):
            issues = [i for i in issues if i["field"] != pi["field"]]
            issues.append(pi)

    # WHY: No fix_suggestion key — batch mode skips LLM for speed
    error_count = sum(1 for i in issues if i["severity"] == "error")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")

    total_checks = len(ALLEGRO_BASE_RULES) + 8
    penalty = (error_count * 2 + warning_count) / max(total_checks, 1) * 100
    score = max(0, round(100 - penalty, 1))

    if error_count > 0:
        overall_status = "error"
    elif warning_count > 0:
        overall_status = "warning"
    else:
        overall_status = "compliant"

    return {
        "source_url": product.source_url,
        "source_id": product.source_id,
        "product_title": product.title,
        "overall_status": overall_status,
        "score": score,
        "issues": issues,
    }


async def audit_product(url: str, marketplace: str) -> Dict:
    """
    Full audit pipeline: scrape → base rules → parameter rules → AI suggestions.
    """
    # Step 1: Scrape based on marketplace
    if marketplace == "allegro":
        return await _audit_allegro(url, marketplace)
    elif marketplace == "amazon":
        return await _audit_amazon(url, marketplace)
    elif marketplace == "ebay":
        return await _audit_ebay(url, marketplace)
    else:
        return _error_response(url, marketplace, f"Marketplace '{marketplace}' nie jest obsługiwany")


def _error_response(url: str, marketplace: str, message: str) -> Dict:
    """Standard error response for audit failures."""
    return {
        "source_url": url, "source_id": "", "marketplace": marketplace,
        "product_title": "", "overall_status": "error", "score": 0,
        "issues": [{"field": "scraper", "severity": "error",
                    "message": message, "fix_suggestion": None}],
        "product_data": {},
    }


def _score_response(url: str, source_id: str, marketplace: str, title: str,
                    issues: List[Dict], product_data: Dict, total_checks: int) -> Dict:
    """Build audit response with score calculation — shared by all marketplaces."""
    error_count = sum(1 for i in issues if i["severity"] == "error")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")

    penalty = (error_count * 2 + warning_count) / max(total_checks, 1) * 100
    score = max(0, round(100 - penalty, 1))

    if error_count > 0:
        overall_status = "error"
    elif warning_count > 0:
        overall_status = "warning"
    else:
        overall_status = "compliant"

    logger.info("audit_completed", url=url, marketplace=marketplace,
                score=score, errors=error_count, warnings=warning_count)

    return {
        "source_url": url, "source_id": source_id, "marketplace": marketplace,
        "product_title": title, "overall_status": overall_status,
        "score": score, "issues": issues, "product_data": product_data,
    }


async def _audit_allegro(url: str, marketplace: str) -> Dict:
    """Allegro audit: scrape → base rules → parameter rules → AI suggestions."""
    product = await scrape_allegro_product(url)
    if product.error:
        return _error_response(url, marketplace, f"Błąd scrapowania: {product.error}")

    fields = _extract_audit_fields(product)
    issues = _run_base_rules(fields, ALLEGRO_BASE_RULES)

    # WHY: Deep Allegro parameter validation (batteries, CE, GPSR, weight, etc.)
    param_issues = validate_allegro_parameters(
        raw_params=product.parameters or {},
        title=product.title or "",
        category=product.category or "",
    )

    # WHY: Deduplicate — keep more specific param rule over base rule
    base_fields = {i["field"] for i in issues}
    for pi in param_issues:
        if pi["field"] not in base_fields:
            issues.append(pi)
        elif pi["severity"] == "error" and any(
            i["field"] == pi["field"] and i["severity"] != "error" for i in issues
        ):
            issues = [i for i in issues if i["field"] != pi["field"]]
            issues.append(pi)

    issues = await _generate_fix_suggestions(issues, product.title)

    product_data = {
        "title": product.title, "price": product.price, "currency": product.currency,
        "ean": product.ean, "brand": product.brand, "manufacturer": product.manufacturer,
        "condition": product.condition, "category": product.category,
        "images": product.images[:5], "parameters_count": len(product.parameters),
        "description_length": len(product.description),
        "parameters": dict(list((product.parameters or {}).items())[:20]),
    }

    return _score_response(
        url, product.source_id, marketplace, product.title, issues,
        product_data, total_checks=len(ALLEGRO_BASE_RULES) + 8,
    )


async def _audit_amazon(url: str, marketplace: str) -> Dict:
    """Amazon audit: parse ASIN/URL → SP-API Catalog Items → base rules → AI suggestions.

    WHY SP-API over scraping: Reliable structured data, no anti-bot issues,
    returns title, bullets, description, images, brand from Amazon's own API.
    """
    listing = parse_amazon_input(url)
    if listing.error:
        return _error_response(url, marketplace, listing.error)

    # WHY: SP-API needs marketplace code (DE, US, etc.) — parse_input extracts it from URL
    mp_code = listing.marketplace or "DE"
    data = await fetch_catalog_item(listing.asin, mp_code)

    if data.get("error"):
        return _error_response(url, marketplace, data["error"])

    fields = {
        "title": data.get("title", ""),
        "bullets": data.get("bullets", []),
        "description": data.get("description", ""),
    }
    issues = _run_base_rules(fields, AMAZON_BASE_RULES)
    issues = await _generate_fix_suggestions(issues, data.get("title", ""))

    product_data = {
        "title": data.get("title"), "asin": listing.asin,
        "marketplace_code": mp_code, "brand": data.get("brand"),
        "manufacturer": data.get("manufacturer"),
        "bullets_count": len(data.get("bullets", [])),
        "bullets": data.get("bullets", [])[:7],
        "images": data.get("images", [])[:5],
        "description_length": len(data.get("description", "")),
    }

    return _score_response(
        listing.url or url, listing.asin, marketplace, data.get("title", ""),
        issues, product_data, total_checks=len(AMAZON_BASE_RULES),
    )


async def _audit_ebay(url: str, marketplace: str) -> Dict:
    """eBay audit: extract item_id → scrape → base rules → AI suggestions."""
    m = re.search(r'/itm/(\d+)', url)
    if not m:
        return _error_response(url, marketplace,
                               "Nie znaleziono ID oferty — wklej link eBay np. ebay.com/itm/123456789")

    item_id = m.group(1)
    data = await fetch_ebay_product(item_id)

    if not data or data.get("error"):
        return _error_response(url, marketplace, data.get("error", "Błąd pobierania danych z eBay"))

    fields = {
        "title": data.get("title") or "",
        "price": str(data.get("price") or ""),
        "listing_active": data.get("listing_active", True),
        "condition": data.get("condition") or "",
    }
    issues = _run_base_rules(fields, EBAY_BASE_RULES)
    issues = await _generate_fix_suggestions(issues, data.get("title", ""))

    product_data = {
        "title": data.get("title"), "price": data.get("price"),
        "currency": data.get("currency"), "condition": data.get("condition"),
        "seller": data.get("seller"), "listing_active": data.get("listing_active"),
        "stock": data.get("stock"),
    }

    return _score_response(
        url, item_id, marketplace, data.get("title", ""),
        issues, product_data, total_checks=len(EBAY_BASE_RULES),
    )
