# backend/schemas/mock_data.py
# Purpose: Pydantic schemas for listings, keywords, competitors, inventory, analytics, settings
# NOT for: DB-backed product schemas — those live in product.py

from pydantic import BaseModel
from typing import Optional
from enum import Enum


# --- Listings ---

class ComplianceStatusEnum(str, Enum):
    compliant = "compliant"
    warning = "warning"
    suppressed = "suppressed"
    blocked = "blocked"


class ListingCreate(BaseModel):
    sku: str
    title: str
    marketplace: str
    compliance_status: ComplianceStatusEnum = ComplianceStatusEnum.compliant
    issues_count: int = 0


class ListingItem(BaseModel):
    id: str
    sku: str
    title: str
    marketplace: str
    compliance_status: ComplianceStatusEnum
    issues_count: int
    last_checked: Optional[str] = None

    class Config:
        from_attributes = True


class ListingsResponse(BaseModel):
    listings: list[ListingItem]
    total: int
    compliant_count: int
    warning_count: int
    suppressed_count: int
    blocked_count: int


# --- Keywords ---

class TrendEnum(str, Enum):
    up = "up"
    down = "down"
    stable = "stable"


class KeywordCreate(BaseModel):
    keyword: str
    marketplace: str
    search_volume: int = 0
    current_rank: Optional[int] = None
    trend: TrendEnum = TrendEnum.stable
    relevance_score: int = 0


class KeywordItem(BaseModel):
    id: str
    keyword: str
    search_volume: int
    current_rank: Optional[int] = None
    marketplace: str
    trend: TrendEnum
    relevance_score: int
    last_updated: Optional[str] = None

    class Config:
        from_attributes = True


class KeywordsResponse(BaseModel):
    keywords: list[KeywordItem]
    total: int
    tracked_count: int
    top_10_count: int
    avg_relevance: float


# --- Competitors ---

class CompetitorStatusEnum(str, Enum):
    winning = "winning"
    losing = "losing"
    tied = "tied"


class CompetitorItem(BaseModel):
    id: str
    competitor_name: str
    asin: str
    product_title: str
    marketplace: str
    their_price: float
    our_price: float
    price_difference: float
    their_rating: float
    their_reviews_count: int
    status: CompetitorStatusEnum
    last_checked: str


class CompetitorsResponse(BaseModel):
    competitors: list[CompetitorItem]
    total: int
    winning_count: int
    losing_count: int
    avg_price_gap: float


# --- Inventory ---

class InventoryStatusEnum(str, Enum):
    in_stock = "in_stock"
    low_stock = "low_stock"
    out_of_stock = "out_of_stock"
    overstock = "overstock"


class InventoryItem(BaseModel):
    id: str
    sku: str
    product_title: str
    marketplace: str
    quantity: int
    reorder_point: int
    days_of_supply: int
    status: InventoryStatusEnum
    unit_cost: float
    total_value: float
    last_restocked: str


class InventoryResponse(BaseModel):
    items: list[InventoryItem]
    total: int
    in_stock_count: int
    low_stock_count: int
    out_of_stock_count: int
    total_value: float


# --- Analytics ---

class MarketplaceRevenue(BaseModel):
    marketplace: str
    revenue: float
    orders: int
    percentage: float


class MonthlyRevenue(BaseModel):
    month: str
    revenue: float
    orders: int


class TopProduct(BaseModel):
    id: str
    title: str
    marketplace: str
    revenue: float
    units_sold: int
    conversion_rate: float


class AnalyticsResponse(BaseModel):
    total_revenue: float
    total_orders: int
    conversion_rate: float
    avg_order_value: float
    revenue_by_marketplace: list[MarketplaceRevenue]
    monthly_revenue: list[MonthlyRevenue]
    top_products: list[TopProduct]


# --- Settings ---

class GeneralSettings(BaseModel):
    store_name: str
    default_marketplace: str
    timezone: str


class MarketplaceConnection(BaseModel):
    id: str
    name: str
    connected: bool
    api_key: str
    last_synced: Optional[str] = None


class NotificationSettings(BaseModel):
    email_alerts: bool
    low_stock_alerts: bool
    competitor_price_changes: bool
    compliance_warnings: bool


class DataExportSettings(BaseModel):
    default_export_format: str
    auto_sync_frequency: str


# WHY: Per-provider API key storage — keys masked on GET, raw on PUT
class LLMProviderConfig(BaseModel):
    api_key: str = ""


class LLMSettings(BaseModel):
    default_provider: str = "groq"
    providers: dict[str, LLMProviderConfig] = {}


# WHY: Persisted GPSR defaults so converter auto-fills them on load
class GPSRSettings(BaseModel):
    manufacturer_contact: str = ""
    manufacturer_address: str = ""
    manufacturer_city: str = ""
    manufacturer_country: str = ""
    country_of_origin: str = ""
    safety_attestation: str = ""
    responsible_person_type: str = ""
    responsible_person_name: str = ""
    responsible_person_address: str = ""
    responsible_person_country: str = ""
    amazon_browse_node: str = ""
    amazon_product_type: str = ""
    ebay_category_id: str = ""
    kaufland_category: str = ""


class SettingsResponse(BaseModel):
    general: GeneralSettings
    marketplace_connections: list[MarketplaceConnection]
    notifications: NotificationSettings
    data_export: DataExportSettings
    llm: Optional[LLMSettings] = None
    gpsr: Optional[GPSRSettings] = None


# --- Dashboard Stats ---

class DashboardStatsResponse(BaseModel):
    total_products: int
    pending_optimization: int
    optimized_products: int
    published_products: int
    failed_products: int
    average_optimization_score: float
    recent_imports: int
    recent_publishes: int
