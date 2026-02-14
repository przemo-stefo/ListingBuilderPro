# backend/services/audit_service.py
# Purpose: Product card audit — scrape → run checks → generate AI fix suggestions
# NOT for: Template file validation (that's compliance/service.py)

import structlog
from typing import List, Dict

from config import settings
from services.scraper.allegro_scraper import scrape_allegro_product, AllegroProduct
from services.compliance.allegro_rules import validate_allegro_parameters

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


async def audit_product(url: str, marketplace: str) -> Dict:
    """
    Full audit pipeline: scrape → base rules → parameter rules → AI suggestions.
    """
    # Step 1: Scrape
    if marketplace == "allegro":
        product = await scrape_allegro_product(url)
    else:
        return {
            "source_url": url, "source_id": "", "marketplace": marketplace,
            "product_title": "", "overall_status": "error", "score": 0,
            "issues": [{"field": "scraper", "severity": "error",
                        "message": f"Scraping dla {marketplace} jeszcze nie dostępny — użyj Allegro URL",
                        "fix_suggestion": None}],
            "product_data": {},
        }

    if product.error:
        return {
            "source_url": url, "source_id": product.source_id,
            "marketplace": marketplace, "product_title": "", "overall_status": "error",
            "score": 0,
            "issues": [{"field": "scraper", "severity": "error",
                        "message": f"Błąd scrapowania: {product.error}",
                        "fix_suggestion": None}],
            "product_data": {},
        }

    # Step 2: Base audit rules (title, images, description, etc.)
    fields = _extract_audit_fields(product)
    issues = _run_base_rules(fields, ALLEGRO_BASE_RULES)

    # Step 3: Deep Allegro parameter validation (batteries, CE, GPSR, weight, etc.)
    param_issues = validate_allegro_parameters(
        raw_params=product.parameters or {},
        title=product.title or "",
        category=product.category or "",
    )

    # WHY: Deduplicate — base rules already check manufacturer/ean at top level,
    # param rules check them in parameters. Keep the more specific param rule.
    base_fields = {i["field"] for i in issues}
    for pi in param_issues:
        if pi["field"] not in base_fields:
            issues.append(pi)
        elif pi["severity"] == "error" and any(
            i["field"] == pi["field"] and i["severity"] != "error" for i in issues
        ):
            # WHY: Upgrade warning → error if param rule is stricter
            issues = [i for i in issues if i["field"] != pi["field"]]
            issues.append(pi)

    # Step 4: AI fix suggestions
    issues = await _generate_fix_suggestions(issues, product.title)

    # Step 5: Calculate score
    error_count = sum(1 for i in issues if i["severity"] == "error")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")

    # WHY: Total possible checks = base rules + estimated param rules
    total_checks = len(ALLEGRO_BASE_RULES) + 8  # 8 key parameter checks
    penalty = (error_count * 2 + warning_count) / max(total_checks, 1) * 100
    score = max(0, round(100 - penalty, 1))

    if error_count > 0:
        overall_status = "error"
    elif warning_count > 0:
        overall_status = "warning"
    else:
        overall_status = "compliant"

    product_data = {
        "title": product.title,
        "price": product.price,
        "currency": product.currency,
        "ean": product.ean,
        "brand": product.brand,
        "manufacturer": product.manufacturer,
        "condition": product.condition,
        "category": product.category,
        "images": product.images[:5],
        "parameters_count": len(product.parameters),
        "description_length": len(product.description),
        # WHY: Include raw parameters for frontend detail view
        "parameters": dict(list((product.parameters or {}).items())[:20]),
    }

    logger.info(
        "audit_completed",
        url=url,
        score=score,
        errors=error_count,
        warnings=warning_count,
        param_issues=len(param_issues),
    )

    return {
        "source_url": url,
        "source_id": product.source_id,
        "marketplace": marketplace,
        "product_title": product.title,
        "overall_status": overall_status,
        "score": score,
        "issues": issues,
        "product_data": product_data,
    }
