// frontend/src/app/demo/amazon-pro/types.ts
// Purpose: TypeScript interfaces for Amazon Pro Demo API responses
// NOT for: Backend models or general app types

export interface DemoKeyword {
  keyword: string
  search_volume: number
  relevance: number
  competition: number
  ranking_juice: number
  priority: 'HIGH' | 'MEDIUM' | 'LOW'
}

export interface DemoProduct {
  asin: string
  marketplace: string
  title: string
  brand: string
  manufacturer: string
  bullets: string[]
  description: string
  images: string[]
  category: string
  price?: string
  currency?: string
  keywords?: DemoKeyword[]
  error?: string | null
}

export interface OptimizedListing {
  title: string
  bullet_points: string[]
  description: string
  backend_keywords?: string
  error?: string
}

export interface CoverageResult {
  before_pct: number
  after_pct: number
  improvement: number
  keywords_covered: number
  keywords_total: number
}

export interface RJComponents {
  keyword_coverage: number
  exact_match_density: number
  search_volume_weighted: number
  backend_efficiency: number
  structure_quality: number
}

export interface ListingDNASnapshot {
  score: number
  grade: string
  verdict: string
  components: RJComponents
  tos_violations: number
  tos_severity: string
  suppression_risk: boolean
}

export interface ListingDNA {
  before: ListingDNASnapshot
  after: ListingDNASnapshot
  improvement: number
  tos_issues_fixed: number
}

export interface TOSViolation {
  rule: string
  severity: 'SUPPRESSION' | 'WARNING'
  message: string
  field: string
}

export interface TOSScan {
  violations: TOSViolation[]
  severity: 'PASS' | 'WARN' | 'FAIL'
  suppression_risk: boolean
  violation_count: number
}

// WHY: Parsed keyword from Helium10/DataDive CSV upload
export interface ParsedKeyword {
  phrase: string
  search_volume: number
  relevancy: number
  ranking_juice: number
  competition: number
  smart_score: number
  indexed: boolean
  word_count: number
}

export interface KeywordUploadResult {
  source: 'datadive' | 'cerebro' | 'magnet' | 'blackbox' | 'generic'
  keywords: ParsedKeyword[]
  products?: Array<{ asin: string; title: string; monthly_revenue: number }>
  stats: {
    total: number
    with_volume: number
    avg_volume: number
    top_keyword: string
    top_rj?: number
  }
  error?: string | null
}

export interface ComplianceIssue {
  field: string
  severity: 'FAIL' | 'WARNING'
  message: string
  regulation: string
}

export interface ComplianceResult {
  status: 'PASS' | 'WARNING' | 'FAIL'
  score: number
  issues: ComplianceIssue[]
  checks_run: number
  summary: {
    fail_count: number
    warning_count: number
    pass_count: number
  }
}

export interface PublishResult {
  status: string
  message?: string
  sku: string
  marketplace: string
  attributes_count?: number
  would_call?: string
}

export interface CouponResult {
  status: string
  message?: string
  coupon?: {
    name: string
    discount_type: string
    discount_value: number
    budget: number
    currency: string
    asins: string[]
    start_date: string
    end_date: string
    estimated_redemptions: number
  }
  would_call?: string
}

// --- Competitor-Inspired Listing Generator ---

export interface ScrapedCompetitor {
  asin: string
  title: string
  bullets: string[]
  description: string
  error?: string | null
}

export interface ListingVersion {
  name: string
  title: string
  bullets: string[]
  description: string
  backend_keywords: string
}

export interface CompetitorInspireResult {
  competitors: ScrapedCompetitor[]
  failed: Array<{ asin: string; error: string }>
  common_keywords: string[]
  versions: ListingVersion[]
  error?: string
}

// --- Amazon Expert Chat ---

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  sources_used?: number
  timestamp: number
}

export interface ChatResponse {
  answer: string
  sources_used: number
  has_context: boolean
  mode: string
  sources: string[]
  error?: string
}

// --- WOW Feature 1: Competitor Compliance Radar ---

export interface CompetitorScanResult {
  competitor: {
    title: string
    brand: string
    asin: string
    bullets: string[]
  }
  tos_scan: TOSScan
  compliance: ComplianceResult
  risk_summary: {
    level: 'HIGH' | 'MEDIUM' | 'LOW'
    message: string
    total_issues: number
    tos_violations: number
    compliance_fails: number
    compliance_warnings: number
    suppression_risk: boolean
  }
}

// --- WOW Feature 2: EFSA Ingredient-to-Claims Mapper ---

export interface EFSAIngredientResult {
  name: string
  found: boolean
  approved_claims: {
    de: string[]
    en: string[]
  }
  forbidden_in_listing: Array<{
    pattern: string
    matched_text: string
  }>
  suggestion: string
}

export interface EFSAClaimsResult {
  ingredients: EFSAIngredientResult[]
  auto_detected: boolean
  summary: {
    total_ingredients: number
    with_efsa_data: number
    forbidden_claims_found: number
    approved_claims_available: number
  }
  error?: string
}

// --- WOW Feature 3: Listing Change Guard ---

export interface ListingGuardChange {
  type: 'TRUNCATION' | 'PROMO_REMOVAL' | 'BRAND_REMOVAL' | 'SEPARATOR_REMOVAL'
  description: string
  impact: 'HIGH' | 'MEDIUM' | 'LOW'
}

export interface ListingGuardResult {
  original: {
    title: string
    bullets: string[]
  }
  amazon_modified: {
    title: string
    bullets: string[]
  }
  changes: ListingGuardChange[]
  rj_impact: {
    before: number
    after: number
    drop: number
    before_grade: string
    after_grade: string
  }
  lost_keywords: Array<{
    keyword: string
    search_volume: number
    ranking_juice: number
  }>
  alert: {
    type: string
    detected_ago: string
    severity: 'HIGH' | 'MEDIUM' | 'LOW'
  }
}
