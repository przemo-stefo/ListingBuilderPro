// frontend/src/lib/types/index.ts
// Purpose: TypeScript types and interfaces for the entire application
// NOT for: Runtime validation or API implementation

// WHY: Must match backend ProductResponse schema exactly (schemas/product.py)
export interface Product {
  id: number
  source_platform: string
  source_id: string
  source_url: string | null
  title_original: string
  title_optimized: string | null
  description_original: string | null
  description_optimized: string | null
  category: string | null
  brand: string | null
  price: number | null
  currency: string
  images: string[]
  attributes: Record<string, unknown>
  status: 'imported' | 'optimizing' | 'optimized' | 'publishing' | 'published' | 'failed'
  optimization_score: number | null
  marketplace_data: Record<string, unknown>
  created_at: string
  updated_at: string | null
}

export interface ProductListResponse {
  items: Product[]
  total: number
  page: number
  page_size: number
  total_pages: number
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
  source_platform?: string
  source_id?: string
  source_url?: string
  title?: string
  description?: string
  price?: number
  brand?: string
  category?: string
  // WHY: Must match backend ProductImport schema field names
  images?: string[]
  attributes?: Record<string, unknown>
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
  source?: string
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
  id: string
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
export type MarketplaceId = 'amazon' | 'ebay' | 'walmart' | 'shopify' | 'allegro' | 'bol'

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
  llm?: LLMSettings
  gpsr?: GPSRData
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

export interface StoreUrlsResponse {
  store_name: string
  urls: string[]
  total: number
  error: string | null
  capped: boolean
}

export interface StoreConvertRequest {
  urls: string[]
  marketplace: string
  gpsr_data: GPSRData
  eur_rate: number
}

export interface StoreJobStatus {
  job_id: string
  status: 'processing' | 'done' | 'failed'
  total: number
  scraped: number
  converted: number
  failed: number
  download_ready: boolean
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

// LLM Provider types
export type LLMProvider = 'groq' | 'gemini_flash' | 'gemini_pro' | 'openai'

export interface LLMProviderConfig {
  api_key: string
}

export interface LLMSettings {
  default_provider: LLMProvider
  providers: Partial<Record<LLMProvider, LLMProviderConfig>>
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
  audience_context?: string
  account_type?: 'seller' | 'vendor'
  // WHY: Multi-LLM — client picks provider and sends their API key
  llm_provider?: LLMProvider
  llm_api_key?: string
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

export interface RankingJuice {
  score: number
  grade: string
  verdict: string
  components: Record<string, number>
  weights: Record<string, number>
}

export interface CoverageBreakdown {
  title_pct: number
  bullets_pct: number
  backend_pct: number
  description_pct: number
}

export interface PPCRecommendation {
  phrase: string
  search_volume: number
  indexed?: boolean
  rationale?: string
}

export interface PPCRecommendations {
  exact_match: PPCRecommendation[]
  phrase_match: PPCRecommendation[]
  broad_match: PPCRecommendation[]
  negative_suggestions: string[]
  summary: {
    exact_count: number
    phrase_count: number
    broad_count: number
    negative_count: number
    estimated_daily_budget_usd: number
  }
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
  ranking_juice?: RankingJuice
  llm_provider?: LLMProvider
  llm_fallback_from?: string | null
  optimization_source?: 'n8n' | 'direct'
  listing_history_id?: string | null
  coverage_breakdown?: CoverageBreakdown
  coverage_target?: number
  meets_coverage_target?: boolean
  ppc_recommendations?: PPCRecommendations
  account_type?: 'seller' | 'vendor'
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

export interface MonitoringSnapshot {
  id: string
  marketplace: string
  product_id: string
  ean: string | null
  snapshot_data: Record<string, unknown>
  created_at: string
}

export interface PollResult {
  marketplace: string
  status: string
  total_snapshots: number
  results: Array<{ product_id: string; status: string; error?: string; title?: string }>
}

// Observability Trace types
export interface TraceItem {
  id: number
  product_title: string
  created_at: string | null
  total_duration_ms: number | null
  total_tokens: number | null
  estimated_cost_usd: number | null
  span_count: number
}

export interface TraceStats {
  runs_with_traces: number
  avg_tokens_per_run: number
  avg_duration_ms: number
  total_cost_usd: number
  total_tokens: number
}

// EPR Report types (matches backend schemas/epr.py)
export interface EprReportRow {
  id: string
  asin: string | null
  marketplace: string | null
  epr_category: string | null
  registration_number: string | null
  paper_kg: number
  glass_kg: number
  aluminum_kg: number
  steel_kg: number
  plastic_kg: number
  wood_kg: number
  units_sold: number
  reporting_period: string | null
}

export interface EprReport {
  id: string
  report_type: string
  marketplace_id: string
  status: string
  sp_api_report_id: string | null
  row_count: number
  error_message: string | null
  created_at: string
  completed_at: string | null
  rows?: EprReportRow[]
}

export interface EprReportsListResponse {
  reports: EprReport[]
  total: number
}

export interface EprStatusResponse {
  credentials_configured: boolean
  has_refresh_token: boolean
}

export interface EprFetchRequest {
  report_type?: string
  marketplace_id?: string
}

// EPR Country Rules types (cross-border compliance)
export interface EprCountryRule {
  id: string
  country_code: string
  country_name: string
  category: string
  registration_required: boolean
  authority_name: string | null
  authority_url: string | null
  threshold_description: string | null
  threshold_units: number | null
  threshold_revenue_eur: number | null
  deadline: string | null
  penalty_description: string | null
  notes: string | null
}

export interface EprCountryRulesListResponse {
  rules: EprCountryRule[]
  total: number
}

// OAuth Connection types
export interface OAuthConnection {
  id: string
  marketplace: string
  status: string
  seller_id: string | null
  seller_name: string | null
  created_at: string | null
}

export interface OAuthConnectionsResponse {
  connections: OAuthConnection[]
}

export interface OAuthAuthorizeResponse {
  authorize_url: string
  state: string
}

// Subscription types (Stripe)
export interface SubscriptionStatus {
  tier: string
  status: string
  stripe_customer_id: string | null
  current_period_end: string | null
  cancel_at_period_end: boolean
}

// Allegro Offers Manager types
export interface AllegroOffer {
  id: string
  name: string
  price: { amount: string; currency: string }
  stock: { available: number }
  status: string
  image?: string
  category?: string
}

export interface AllegroOffersListResponse {
  offers: AllegroOffer[]
  total: number
}

export interface AllegroOfferDetail {
  source_url: string
  source_id: string
  title: string
  description: string
  price: string
  currency: string
  ean: string
  images: string[]
  category: string
  quantity: string
  condition: string
  parameters: Record<string, string>
  brand: string
  manufacturer: string
  error: string | null
}

export interface BulkCommandResponse {
  command_id: string
  status: string
  count: number
}

export interface AllegroOfferUpdateRequest {
  name?: string
  price?: { amount: string; currency: string }
  description_html?: string
}

export interface AllegroOffersParams {
  limit?: number
  offset?: number
  status?: string
  search?: string
}

export interface AllegroBulkPriceChange {
  offer_id: string
  price: string
  currency: string
}

// Audience Research types (OV Skills via n8n)
export interface AudienceResearchRequest {
  product: string
  audience?: string
  skill?: 'deep-customer-research' | 'icp-discovery' | 'creative-brief'
}

export interface AudienceResearchResponse {
  skill: string
  product: string
  audience: string
  result: string
  tokens_used: number
  model: string
  cost: string
}

// Listing Score types (used by /listing-score page and auto-score in optimizer)
export interface DimensionScore {
  name: string
  score: number
  explanation: string
  tip: string
}

export interface ScoreResult {
  overall_score: number
  dimensions: DimensionScore[]
  sources_used: number
}

// Listing Changes types (field-level change tracking)
export interface ListingChange {
  id: string
  tracked_product_id: string | null
  user_id: string
  marketplace: string
  product_id: string
  change_type: 'title' | 'bullets' | 'description' | 'images' | 'price' | 'brand'
  field_name: string | null
  old_value: string | null
  new_value: string | null
  detected_at: string
}

export interface ListingChangesResponse {
  items: ListingChange[]
  total: number
  limit: number
  offset: number
}

export interface ListingChangeSummary {
  product_id: string
  marketplace: string
  change_count: number
  last_change: string | null
}

// Error types
export interface ApiError {
  message: string
  code?: string
  details?: Record<string, unknown>
}
