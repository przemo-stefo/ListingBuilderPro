# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/services/compliance/rules.py
# Purpose: Marketplace-specific compliance rules and validation engine (32 rules)
# NOT for: File parsing, database operations, or API routing

from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger()


# ── Rule definitions ──────────────────────────────────────────────────────────
# Each rule is a dict with: field, check_type, severity, message, and optional params.
#
# check_type meanings:
#   "required"     — field must be non-empty
#   "required_if"  — field required when trigger_field is non-empty
#   "not_empty"    — warning if empty (softer than required)
#   "value_in"     — value must be in allowed_values list (case-insensitive)


AMAZON_RULES = [
    # ── GPSR / Manufacturer (always required) ──
    {
        "field": "manufacturer",
        "check_type": "required",
        "severity": "error",
        "message": "Manufacturer name is required for GPSR compliance",
    },
    {
        "field": "manufacturer_contact_information",
        "check_type": "required",
        "severity": "error",
        "message": "Manufacturer contact information is required for GPSR",
    },
    {
        "field": "country_of_origin",
        "check_type": "required",
        "severity": "error",
        "message": "Country of origin is required",
    },
    {
        "field": "gpsr_safety_attestation",
        "check_type": "not_empty",
        "severity": "warning",
        "message": "GPSR safety attestation recommended for EU compliance",
    },
    {
        "field": "gpsr_manufacturer_reference_email_address",
        "check_type": "not_empty",
        "severity": "warning",
        "message": "GPSR manufacturer reference email recommended",
    },
    # ── Batteries (required_if batteries_required is set) ──
    # WHY battery_type1: Amazon templates use numbered suffixes (battery_type1, battery_type2, etc.)
    # We check the "1" variant since at least the primary battery must be declared.
    {
        "field": "battery_type1",
        "check_type": "required_if",
        "trigger_field": "batteries_required",
        "severity": "error",
        "message": "Battery type required when batteries_required is set",
    },
    {
        "field": "number_of_batteries1",
        "check_type": "required_if",
        "trigger_field": "batteries_required",
        "severity": "error",
        "message": "Number of batteries required when batteries_required is set",
    },
    {
        "field": "lithium_battery_packaging",
        "check_type": "required_if",
        "trigger_field": "batteries_required",
        "severity": "error",
        "message": "Lithium battery packaging info required when batteries_required is set",
    },
    # ── Hazmat / GHS (required_if ghs_classification_class1 is set) ──
    # WHY ghs_classification_class1: Amazon uses numbered GHS fields.
    # Some category templates omit signal_word/hazard_statements entirely —
    # the rule gracefully skips when neither field nor trigger exist.
    {
        "field": "ghs_signal_word",
        "check_type": "required_if",
        "trigger_field": "ghs_classification_class1",
        "severity": "error",
        "message": "GHS signal word required when GHS classification is set",
    },
    {
        "field": "hazard_statements",
        "check_type": "required_if",
        "trigger_field": "ghs_classification_class1",
        "severity": "error",
        "message": "Hazard statements required when GHS classification is set",
    },
    {
        "field": "precautionary_statements",
        "check_type": "required_if",
        "trigger_field": "ghs_classification_class1",
        "severity": "error",
        "message": "Precautionary statements required when GHS classification is set",
    },
    {
        "field": "ghs_pictogram",
        "check_type": "required_if",
        "trigger_field": "ghs_classification_class1",
        "severity": "error",
        "message": "GHS pictogram required when GHS classification is set",
    },
    # ── Dangerous goods (required_if supplier_declared_dg_hz_regulation1 is set) ──
    {
        "field": "un_number",
        "check_type": "required_if",
        "trigger_field": "supplier_declared_dg_hz_regulation1",
        "severity": "error",
        "message": "UN number required when DG/HZ regulation is declared",
    },
    {
        "field": "safety_data_sheet_url",
        "check_type": "required_if",
        "trigger_field": "supplier_declared_dg_hz_regulation1",
        "severity": "error",
        "message": "Safety data sheet URL required when DG/HZ regulation is declared",
    },
]


EBAY_RULES = [
    # ── Manufacturer info (always required for EU) ──
    {
        "field": "Manufacturer Name",
        "check_type": "required",
        "severity": "error",
        "message": "Manufacturer name is required for EU product safety",
    },
    {
        # WHY "AddressLine1" not "Address Line 1": eBay templates use no space before "Line"
        "field": "Manufacturer AddressLine1",
        "check_type": "required",
        "severity": "error",
        "message": "Manufacturer address is required",
    },
    {
        "field": "Manufacturer City",
        "check_type": "required",
        "severity": "error",
        "message": "Manufacturer city is required",
    },
    {
        "field": "Manufacturer Country",
        "check_type": "required",
        "severity": "error",
        "message": "Manufacturer country is required",
    },
    # ── Responsible Person (EU GPSR) ──
    {
        "field": "Responsible Person 1 Type",
        "check_type": "required",
        "severity": "error",
        "message": "Responsible Person type is required for GPSR",
    },
    {
        # WHY "AddressLine1": Same eBay naming convention as Manufacturer AddressLine1
        "field": "Responsible Person 1 AddressLine1",
        "check_type": "required",
        "severity": "error",
        "message": "Responsible Person address is required for GPSR",
    },
    {
        "field": "Responsible Person 1 Country",
        "check_type": "required",
        "severity": "error",
        "message": "Responsible Person country is required for GPSR",
    },
    # ── Product compliance policy ──
    {
        "field": "ProductCompliancePolicyID",
        "check_type": "not_empty",
        "severity": "warning",
        "message": "Product compliance policy ID recommended",
    },
    # ── Hazmat (required_if HazmatPictogramID is set) ──
    {
        "field": "HazmatSignalWord",
        "check_type": "required_if",
        "trigger_field": "HazmatPictogramID",
        "severity": "error",
        "message": "Hazmat signal word required when pictogram is set",
    },
    # ── Take-back / WEEE ──
    {
        "field": "TakeBackPolicyID",
        "check_type": "not_empty",
        "severity": "warning",
        "message": "Take-back policy ID recommended for electronics/WEEE compliance",
    },
    # ── Safety pictograms ──
    # WHY "Product Safety Pictograms": eBay template header name (not "SafetyPictogramID")
    {
        "field": "Product Safety Pictograms",
        "check_type": "not_empty",
        "severity": "warning",
        "message": "Safety pictogram recommended when product has safety concerns",
    },
]


KAUFLAND_RULES = [
    # ── Safety guidelines / precautionary (mutual dependency) ──
    {
        "field": "precautionary_statements",
        "check_type": "required_if",
        "trigger_field": "safety_guidelines",
        "severity": "error",
        "message": "Precautionary statements required when safety guidelines are set",
    },
    {
        "field": "safety_guidelines",
        "check_type": "required_if",
        "trigger_field": "precautionary_statements",
        "severity": "error",
        "message": "Safety guidelines required when precautionary statements are set",
    },
    # ── Energy efficiency ──
    {
        "field": "energy_efficiency_class_2021",
        "check_type": "value_in",
        "allowed_values": ["a", "b", "c", "d", "e", "f", "g", ""],
        "severity": "warning",
        "message": "Energy efficiency class must be A-G (EU 2021 scale)",
    },
    # ── Age restriction (required_if age_recommendation is set) ──
    {
        "field": "fsk",
        "check_type": "required_if",
        "trigger_field": "age_recommendation",
        "severity": "error",
        "message": "FSK age rating required when age recommendation is set",
    },
    # ── Batteries ──
    {
        "field": "contains_batteries",
        "check_type": "value_in",
        "allowed_values": ["yes", "no", ""],
        "severity": "warning",
        "message": "Contains batteries must be 'yes' or 'no'",
    },
    # ── Hazard warnings ──
    {
        "field": "signal_word",
        "check_type": "required_if",
        "trigger_field": "hazard_pictograms",
        "severity": "error",
        "message": "Signal word required when hazard pictograms are set",
    },
    {
        "field": "hazard_statements",
        "check_type": "required_if",
        "trigger_field": "hazard_pictograms",
        "severity": "error",
        "message": "Hazard statements required when hazard pictograms are set",
    },
]

# Map marketplace name → rule set
RULES_BY_MARKETPLACE = {
    "amazon": AMAZON_RULES,
    "ebay": EBAY_RULES,
    "kaufland": KAUFLAND_RULES,
}


def validate_row(product: Dict[str, str], marketplace: str) -> List[Dict[str, Any]]:
    """
    Run all rules for a marketplace against one product row.

    Returns list of issue dicts: [{field, rule, severity, message}, ...]
    Empty list = product is fully compliant.
    """
    rules = RULES_BY_MARKETPLACE.get(marketplace, [])
    issues = []

    for rule in rules:
        issue = _check_rule(product, rule)
        if issue:
            issues.append(issue)

    return issues


def _check_rule(product: Dict[str, str], rule: Dict) -> Optional[Dict[str, Any]]:
    """
    Evaluate a single rule against a product row.
    Returns an issue dict if the rule is violated, None if OK.
    """
    field = rule["field"]
    check_type = rule["check_type"]
    value = product.get(field, "").strip()

    if check_type == "required":
        # Field must be non-empty
        if not value:
            return _make_issue(field, check_type, rule)

    elif check_type == "not_empty":
        # Softer check — only produces warning/info
        if not value:
            return _make_issue(field, check_type, rule)

    elif check_type == "required_if":
        # Field required when trigger_field has a value
        trigger_field = rule["trigger_field"]
        trigger_value = product.get(trigger_field, "").strip()
        if trigger_value and not value:
            return _make_issue(field, check_type, rule)

    elif check_type == "value_in":
        # If field has a value, it must be in the allowed list
        allowed = rule.get("allowed_values", [])
        if value and value.lower() not in [v.lower() for v in allowed]:
            return _make_issue(field, check_type, rule)

    return None


def _make_issue(field: str, rule_type: str, rule: Dict) -> Dict[str, Any]:
    """Build a standardized issue dict from a rule violation."""
    return {
        "field": field,
        "rule": rule_type,
        "severity": rule["severity"],
        "message": rule["message"],
    }
