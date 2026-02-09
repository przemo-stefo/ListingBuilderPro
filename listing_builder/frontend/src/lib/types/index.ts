// frontend/src/lib/types/index.ts
// Purpose: TypeScript types and interfaces for the entire application
// NOT for: Runtime validation or API implementation

// Product types
export interface Product {
  id: string
  asin?: string
  title: string
  description: string
  bullet_points: string[]
  price?: number
  brand?: string
  category?: string
  image_urls?: string[]
  status: 'pending' | 'optimized' | 'published' | 'error'
  marketplace?: string
  created_at: string
  updated_at: string
  optimization_score?: number
  seo_keywords?: string[]
}

export interface ProductListResponse {
  items: Product[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

// Import types
export interface ImportJobStatus {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  total_items?: number
  processed_items?: number
  created_at: string
  completed_at?: string
  error?: string
}

export interface SingleProductImport {
  asin?: string
  title: string
  description: string
  bullet_points: string[]
  price?: number
  brand?: string
  category?: string
  image_urls?: string[]
}

export interface BatchProductImport {
  products: SingleProductImport[]
}

// AI Optimization types
export interface OptimizationRequest {
  product_id: string
  marketplace?: string
  target_keywords?: string[]
}

export interface OptimizationResponse {
  product_id: string
  original_title?: string
  optimized_title?: string
  original_description?: string
  optimized_description?: string
  optimization_score: number
  seo_improvements: string[]
  keyword_density: Record<string, number>
}

export interface BatchOptimizationRequest {
  product_ids: string[]
  marketplace?: string
  target_keywords?: string[]
}

// Export/Publishing types
export interface PublishRequest {
  product_id: string
  marketplace: string
  publish_immediately?: boolean
}

export interface PublishResponse {
  product_id: string
  marketplace: string
  status: 'success' | 'failed'
  published_url?: string
  error?: string
}

export interface BulkPublishRequest {
  product_ids: string[]
  marketplace: string
  publish_immediately?: boolean
}

export interface BulkPublishResponse {
  successful: string[]
  failed: Array<{
    product_id: string
    error: string
  }>
  total: number
}

export interface Marketplace {
  id: string
  name: string
  region: string
  requires_approval: boolean
  supported_categories: string[]
}

// Dashboard stats
export interface DashboardStats {
  total_products: number
  pending_optimization: number
  optimized_products: number
  published_products: number
  failed_products: number
  average_optimization_score: number
  recent_imports: number
  recent_publishes: number
}

// Filter types
export interface ProductFilters {
  status?: Product['status']
  marketplace?: string
  search?: string
  min_score?: number
  max_score?: number
  sort_by?: 'created_at' | 'updated_at' | 'optimization_score' | 'title'
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

// API Response wrapper
export interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
}

// Compliance & Listings types
export type ComplianceStatus = 'compliant' | 'warning' | 'suppressed' | 'blocked'

export interface ListingItem {
  sku: string
  title: string
  marketplace: string
  compliance_status: ComplianceStatus
  issues_count: number
  last_checked: string
}

export interface ListingsResponse {
  listings: ListingItem[]
  total: number
  compliant_count: number
  warning_count: number
  suppressed_count: number
  blocked_count: number
}

export interface GetListingsParams {
  marketplace?: string
  compliance_status?: ComplianceStatus
}

// Keyword tracking types
export type KeywordTrend = 'up' | 'down' | 'stable'

export interface KeywordItem {
  id: string
  keyword: string
  search_volume: number
  current_rank: number | null
  marketplace: string
  trend: KeywordTrend
  relevance_score: number
  last_updated: string
}

export interface KeywordsResponse {
  keywords: KeywordItem[]
  total: number
  tracked_count: number
  top_10_count: number
  avg_relevance: number
}

export interface GetKeywordsParams {
  marketplace?: string
  search?: string
}

// Competitor tracking types
export type CompetitorStatus = 'winning' | 'losing' | 'tied'

export interface CompetitorItem {
  id: string
  competitor_name: string
  asin: string
  product_title: string
  marketplace: string
  their_price: number
  our_price: number
  price_difference: number
  their_rating: number
  their_reviews_count: number
  status: CompetitorStatus
  last_checked: string
}

export interface CompetitorsResponse {
  competitors: CompetitorItem[]
  total: number
  winning_count: number
  losing_count: number
  avg_price_gap: number
}

export interface GetCompetitorsParams {
  marketplace?: string
  search?: string
}

// Inventory tracking types
export type StockStatus = 'in_stock' | 'low_stock' | 'out_of_stock' | 'overstock'

export interface InventoryItem {
  id: string
  sku: string
  product_title: string
  marketplace: string
  quantity: number
  reorder_point: number
  days_of_supply: number
  status: StockStatus
  unit_cost: number
  total_value: number
  last_restocked: string
}

export interface InventoryResponse {
  items: InventoryItem[]
  total: number
  in_stock_count: number
  low_stock_count: number
  out_of_stock_count: number
  total_value: number
}

export interface GetInventoryParams {
  marketplace?: string
  status?: StockStatus
  search?: string
}

// Analytics types
export interface MarketplaceRevenue {
  marketplace: string
  revenue: number
  orders: number
  percentage: number
}

export interface MonthlyRevenue {
  month: string
  revenue: number
  orders: number
}

export interface TopProduct {
  id: string
  title: string
  marketplace: string
  revenue: number
  units_sold: number
  conversion_rate: number
}

export interface AnalyticsResponse {
  total_revenue: number
  total_orders: number
  conversion_rate: number
  avg_order_value: number
  revenue_by_marketplace: MarketplaceRevenue[]
  monthly_revenue: MonthlyRevenue[]
  top_products: TopProduct[]
}

export interface GetAnalyticsParams {
  marketplace?: string
  period?: '7d' | '30d' | '90d' | '12m'
}

// Settings types
export type MarketplaceId = 'amazon' | 'ebay' | 'walmart' | 'shopify' | 'allegro'

export interface MarketplaceConnection {
  id: MarketplaceId
  name: string
  connected: boolean
  api_key: string
  last_synced: string | null
}

export interface NotificationSettings {
  email_alerts: boolean
  low_stock_alerts: boolean
  competitor_price_changes: boolean
  compliance_warnings: boolean
}

export type ExportFormat = 'csv' | 'json' | 'excel'
export type SyncFrequency = 'manual' | '1h' | '6h' | '12h' | '24h'

export interface GeneralSettings {
  store_name: string
  default_marketplace: MarketplaceId
  timezone: string
}

export interface DataExportSettings {
  default_export_format: ExportFormat
  auto_sync_frequency: SyncFrequency
}

export interface SettingsResponse {
  general: GeneralSettings
  marketplace_connections: MarketplaceConnection[]
  notifications: NotificationSettings
  data_export: DataExportSettings
}

// WHY: Partial so each section can be saved independently
export type UpdateSettingsPayload = Partial<SettingsResponse>

// Converter types
export interface ConverterMarketplace {
  id: string
  name: string
  format: string
  extension: string
  description: string
}

export interface GPSRData {
  manufacturer_contact: string
  manufacturer_address: string
  manufacturer_city: string
  manufacturer_country: string
  country_of_origin: string
  safety_attestation: string
  responsible_person_type: string
  responsible_person_name: string
  responsible_person_address: string
  responsible_person_country: string
  amazon_browse_node: string
  amazon_product_type: string
  ebay_category_id: string
  kaufland_category: string
}

export interface ConvertRequest {
  urls: string[]
  marketplace: string
  gpsr_data: GPSRData
  eur_rate: number
  delay: number
}

export interface ConvertedProductResult {
  source_url: string
  source_id: string
  fields: Record<string, string>
  warnings: string[]
  error: string | null
}

export interface ConvertResponse {
  total: number
  succeeded: number
  failed: number
  marketplace: string
  products: ConvertedProductResult[]
  warnings: string[]
}

export interface ScrapeResponse {
  total: number
  succeeded: number
  failed: number
  products: Record<string, unknown>[]
}

// Compliance Guard types — file upload → per-product validation report
export type ComplianceSeverity = 'error' | 'warning' | 'info'
export type ComplianceItemStatus = 'compliant' | 'warning' | 'error'

export interface ComplianceIssue {
  field: string
  rule: string
  severity: ComplianceSeverity
  message: string
}

export interface ComplianceItemResult {
  row_number: number
  sku: string
  product_title: string
  status: ComplianceItemStatus
  issues: ComplianceIssue[]
}

// WHY: Full report includes items array — used for detail view
export interface ComplianceReportResponse {
  id: string
  marketplace: string
  filename: string
  total_products: number
  compliant_count: number
  warning_count: number
  error_count: number
  overall_score: number
  created_at: string
  items: ComplianceItemResult[]
}

// WHY: Summary omits items — lighter payload for the reports list table
export interface ComplianceReportSummary {
  id: string
  marketplace: string
  filename: string
  total_products: number
  compliant_count: number
  warning_count: number
  error_count: number
  overall_score: number
  created_at: string
}

export interface ComplianceReportsListResponse {
  items: ComplianceReportSummary[]
  total: number
  limit: number
  offset: number
}

// Listing Optimizer types (n8n workflow)
export interface OptimizerKeyword {
  phrase: string
  search_volume: number
}

export interface OptimizerRequest {
  product_title: string
  brand: string
  product_line?: string
  keywords: OptimizerKeyword[]
  marketplace: string
  mode: 'aggressive' | 'standard'
  language?: string
  asin?: string
  category?: string
}

export interface OptimizerListing {
  title: string
  bullet_points: string[]
  description: string
  backend_keywords: string
}

export interface OptimizerScores {
  coverage_pct: number
  coverage_mode: string
  exact_matches_in_title: number
  title_coverage_pct: number
  backend_utilization_pct: number
  backend_byte_size: number
  compliance_status: string
}

export interface OptimizerCompliance {
  status: string
  errors: string[]
  warnings: string[]
  error_count: number
  warning_count: number
}

export interface OptimizerKeywordIntel {
  total_analyzed: number
  tier1_title: number
  tier2_bullets: number
  tier3_backend: number
  missing_keywords: string[]
  root_words: Array<{ word: string; frequency: number }>
}

export interface OptimizerResponse {
  status: string
  marketplace: string
  brand: string
  mode: string
  language: string
  listing: OptimizerListing
  scores: OptimizerScores
  compliance: OptimizerCompliance
  keyword_intel: OptimizerKeywordIntel
}

// Batch Optimizer types — multiple products in one request
export interface BatchOptimizerRequest {
  products: OptimizerRequest[]
}

export interface BatchOptimizerResult {
  product_title: string
  status: 'completed' | 'error'
  error?: string
  result?: OptimizerResponse
}

export interface BatchOptimizerResponse {
  total: number
  succeeded: number
  failed: number
  results: BatchOptimizerResult[]
}

// WHY: Parsed product from CSV/paste before it becomes an OptimizerRequest
export interface ParsedBatchProduct {
  product_title: string
  brand: string
  keywords: string[]
  product_line?: string
  asin?: string
  category?: string
}

// Optimization History types
export interface OptimizationHistoryItem {
  id: number
  product_title: string
  brand: string
  marketplace: string
  mode: string
  coverage_pct: number
  compliance_status: string
  created_at: string
}

export interface OptimizationHistoryList {
  items: OptimizationHistoryItem[]
  total: number
  page: number
}

// WHY: Detail includes full response for reload
export interface OptimizationHistoryDetail extends OptimizationHistoryItem {
  request_data: OptimizerRequest
  response_data: OptimizerResponse
}

// Monitoring types
export interface MonitoringDashboardStats {
  tracked_products: number
  active_alerts: number
  alerts_today: number
  last_poll: string | null
  marketplaces: Record<string, number>
}

export interface TrackedProduct {
  id: string
  marketplace: string
  product_id: string
  product_url: string | null
  product_title: string | null
  poll_interval_hours: number
  enabled: boolean
  created_at: string
}

export interface TrackProductRequest {
  marketplace: string
  product_id: string
  product_url?: string
  product_title?: string
  poll_interval_hours?: number
}

export interface AlertConfig {
  id: string
  alert_type: string
  name: string
  enabled: boolean
  threshold: number | null
  marketplace: string | null
  email: string | null
  webhook_url: string | null
  cooldown_minutes: number
  last_triggered: string | null
  created_at: string
}

export interface AlertConfigCreateRequest {
  alert_type: string
  name: string
  enabled?: boolean
  threshold?: number
  marketplace?: string
  cooldown_minutes?: number
  webhook_url?: string
}

export interface MonitoringAlert {
  id: string
  config_id: string | null
  alert_type: string
  severity: string
  title: string
  message: string
  details: Record<string, unknown>
  triggered_at: string
  acknowledged: boolean
  acknowledged_at: string | null
}

// Error types
export interface ApiError {
  message: string
  code?: string
  details?: Record<string, unknown>
}
