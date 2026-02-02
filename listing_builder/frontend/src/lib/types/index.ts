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

// Error types
export interface ApiError {
  message: string
  code?: string
  details?: Record<string, unknown>
}
