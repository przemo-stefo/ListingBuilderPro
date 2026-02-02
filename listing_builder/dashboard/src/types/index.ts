// src/types/index.ts
// Purpose: TypeScript type definitions for Compliance Guard
// NOT for: Business logic or API calls

// Enums
export type Marketplace = 'amazon' | 'ebay' | 'allegro' | 'kaufland' | 'temu';
export type AlertType = 'buy_box_lost' | 'low_stock' | 'returns_spike' | 'negative_review' | 'price_anomaly' | 'listing_suppressed' | 'policy_violation' | 'competitor_price';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'dismissed';

// Inventory
export interface InventoryItem {
  sku: string;
  marketplace: Marketplace;
  title: string;
  quantity: number;
  price: number;
  asin?: string;
  listing_id?: string;
  fulfillment_channel?: string;
  condition?: string;
  last_updated: string;
}

export interface InventoryResponse {
  items: InventoryItem[];
  total: number;
  limit: number;
  offset: number;
}

// Buy Box
export interface BuyBoxStatus {
  asin: string;
  sku?: string;
  title?: string;
  has_buy_box: boolean;
  your_price: number;
  buy_box_price: number;
  competitor_price?: number;
  price_difference?: number;
  last_checked: string;
}

export interface BuyBoxResponse {
  items: BuyBoxStatus[];
  total: number;
  winning_count: number;
  losing_count: number;
}

// Alerts
export interface Alert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  status: AlertStatus;
  marketplace: Marketplace;
  sku: string;
  title: string;
  message: string;
  created_at: string;
  data?: Record<string, unknown>;
}

export interface AlertsResponse {
  alerts: Alert[];
  total: number;
  limit: number;
  offset: number;
}

export interface AlertCounts {
  total: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  by_marketplace: Record<string, number>;
}

// Dashboard
export interface AlertSummary {
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  active: number;
}

export interface InventorySummary {
  total_skus: number;
  total_units: number;
  low_stock_count: number;
  out_of_stock_count: number;
  total_value: number;
}

export interface BuyBoxSummary {
  total_asins: number;
  winning_count: number;
  losing_count: number;
  win_rate: number;
}

export interface MarketplaceSummary {
  marketplace: string;
  connected: boolean;
  inventory_count: number;
  active_alerts: number;
  health_score: number;
}

export interface DashboardSummary {
  health_score: number;
  alerts: AlertSummary;
  inventory: InventorySummary;
  buy_box: BuyBoxSummary;
  marketplaces: MarketplaceSummary[];
  last_updated: string;
}

export interface DashboardHistoryPoint {
  date: string;
  health_score: number;
  alert_count: number;
  inventory_value: number;
}

export interface DashboardHistoryResponse {
  history: DashboardHistoryPoint[];
  period_days: number;
}

// Metrics
export interface SellerMetrics {
  marketplace: string;
  feedback_score?: number;
  seller_rating?: number;
  return_rate: number;
  defect_rate: number;
  late_shipment_rate?: number;
  cancellation_rate?: number;
  order_count_30d: number;
  revenue_30d: number;
  last_updated: string;
}

export interface MetricsResponse {
  metrics: SellerMetrics[];
  total_orders_30d: number;
  total_revenue_30d: number;
}
