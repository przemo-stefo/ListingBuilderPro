# backend/services/alert_type_registry.py
# Purpose: Single source of truth for all alert types (Sellerboard-style)
# NOT for: Alert evaluation logic, scheduling, or DB persistence

from typing import List, Dict

# WHY: Centralized registry so both API and future evaluators share same definitions.
# data_source marks what's needed to check this alert type.

ALERT_TYPES: List[Dict] = [
    # ── Product Alerts ──
    {"type": "product.listing_closed", "label": "Listing closed / suppressed", "category": "product", "data_source": "keepa", "default_priority": "critical"},
    {"type": "product.sellers_count_changed", "label": "Sellers count changed", "category": "product", "data_source": "keepa", "default_priority": "major"},
    {"type": "product.price_changed", "label": "Price changed", "category": "product", "data_source": "keepa", "default_priority": "major"},
    {"type": "product.buy_box_lost", "label": "Buy Box lost", "category": "product", "data_source": "keepa", "default_priority": "critical"},
    {"type": "product.asin_lost_parent", "label": "ASIN lost parent", "category": "product", "data_source": "sp-api", "default_priority": "critical"},
    {"type": "product.brand_changed", "label": "Brand changed", "category": "product", "data_source": "sp-api", "default_priority": "major"},
    {"type": "product.category_changed", "label": "Category changed", "category": "product", "data_source": "sp-api", "default_priority": "minor"},
    {"type": "product.dimensions_changed", "label": "Dimensions changed", "category": "product", "data_source": "sp-api", "default_priority": "minor"},
    {"type": "product.listing_text_changed", "label": "Listing text changed", "category": "product", "data_source": "sp-api", "default_priority": "major"},
    {"type": "product.title_changed", "label": "Title changed", "category": "product", "data_source": "sp-api", "default_priority": "major"},
    {"type": "product.main_image_changed", "label": "Main image changed", "category": "product", "data_source": "sp-api", "default_priority": "major"},
    {"type": "product.new_parent_or_child", "label": "New parent / child variation", "category": "product", "data_source": "sp-api", "default_priority": "major"},
    {"type": "product.stock_low", "label": "Stock running low", "category": "product", "data_source": "sp-api", "default_priority": "critical"},

    # ── Financial Alerts ──
    {"type": "financial.large_order", "label": "Unusually large order", "category": "financial", "data_source": "sp-api", "default_priority": "major"},
    {"type": "financial.commission_changed", "label": "Referral fee changed", "category": "financial", "data_source": "sp-api", "default_priority": "major"},
    {"type": "financial.fba_fee_changed", "label": "FBA fee changed", "category": "financial", "data_source": "sp-api", "default_priority": "major"},
    {"type": "financial.reimbursement_possible", "label": "Reimbursement opportunity", "category": "financial", "data_source": "sp-api", "default_priority": "minor"},
    {"type": "financial.size_reduction_opportunity", "label": "Size tier reduction possible", "category": "financial", "data_source": "sp-api", "default_priority": "minor"},
    {"type": "financial.high_return_rate", "label": "High return rate detected", "category": "financial", "data_source": "sp-api", "default_priority": "critical"},

    # ── Performance Alerts ──
    {"type": "performance.rating_dropped", "label": "Rating dropped", "category": "performance", "data_source": "keepa", "default_priority": "major"},
    {"type": "performance.review_spike_negative", "label": "Spike in negative reviews", "category": "performance", "data_source": "sp-api", "default_priority": "critical"},
    {"type": "performance.conversion_rate_drop", "label": "Conversion rate drop", "category": "performance", "data_source": "sp-api", "default_priority": "major"},
    {"type": "performance.sessions_drop", "label": "Sessions / traffic drop", "category": "performance", "data_source": "sp-api", "default_priority": "major"},
    {"type": "performance.advertising_anomaly", "label": "Advertising spend anomaly", "category": "performance", "data_source": "sp-api", "default_priority": "major"},
]

# WHY: Fast lookup by type string (used in routes for validation)
ALERT_TYPE_MAP: Dict[str, Dict] = {a["type"]: a for a in ALERT_TYPES}

CATEGORIES = ["product", "financial", "performance"]

# WHY: SP-API content types now active — listing diff engine detects these
_SP_API_ACTIVE = {
    "product.title_changed", "product.listing_text_changed",
    "product.main_image_changed", "product.brand_changed",
}
ACTIVE_TYPES = {a["type"] for a in ALERT_TYPES if a["data_source"] == "keepa"} | _SP_API_ACTIVE
