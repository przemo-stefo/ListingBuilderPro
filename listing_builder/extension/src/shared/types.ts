// extension/src/shared/types.ts
// Purpose: Shared TypeScript types for the extension
// NOT for: Backend or frontend types

export type Marketplace = "amazon" | "allegro" | "ebay" | "kaufland";

export interface ProductData {
  marketplace: Marketplace;
  productId: string; // ASIN, item ID, offer ID, etc.
  title: string;
  price: string;
  brand: string;
  url: string;
  imageUrl?: string;
}

export interface OptimizationResult {
  title: string;
  bullets: string[];
  description: string;
  backend_keywords: string;
  ranking_juice: number;
  trace?: Record<string, unknown>;
  listing_history_id?: string;
}

export interface Alert {
  id: string;
  product_id: string;
  alert_type: string;
  message: string;
  severity: "high" | "medium" | "low";
  created_at: string;
  is_read: boolean;
}

export interface TrackedProduct {
  id: string;
  marketplace: string;
  product_id: string;
  product_name: string;
  current_price: number | null;
  url: string;
  created_at: string;
}

export interface MonitorStats {
  tracked_count: number;
  alerts_today: number;
  unread_alerts: number;
}
