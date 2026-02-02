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

// Error types
export interface ApiError {
  message: string
  code?: string
  details?: Record<string, unknown>
}
