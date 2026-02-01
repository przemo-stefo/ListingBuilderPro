// src/lib/api.ts
// Purpose: API client for Compliance Guard backend
// NOT for: UI components or state management

import type {
  DashboardSummary,
  DashboardHistoryResponse,
  InventoryResponse,
  BuyBoxResponse,
  AlertsResponse,
  AlertCounts,
  Alert,
  Marketplace,
  AlertType,
  AlertSeverity,
  AlertStatus,
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'test-api-key';

// Generic fetch wrapper with error handling
async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_URL}${endpoint}`;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// =============================================================================
// DASHBOARD
// =============================================================================

export async function getDashboard(): Promise<DashboardSummary> {
  return fetchAPI<DashboardSummary>('/api/dashboard');
}

export async function getDashboardHistory(days = 7): Promise<DashboardHistoryResponse> {
  return fetchAPI<DashboardHistoryResponse>(`/api/dashboard/history?days=${days}`);
}

// =============================================================================
// INVENTORY
// =============================================================================

export interface GetInventoryParams {
  marketplace?: Marketplace;
  low_stock?: boolean;
  threshold?: number;
  limit?: number;
  offset?: number;
}

export async function getInventory(params: GetInventoryParams = {}): Promise<InventoryResponse> {
  const searchParams = new URLSearchParams();

  if (params.marketplace) searchParams.set('marketplace', params.marketplace);
  if (params.low_stock) searchParams.set('low_stock', 'true');
  if (params.threshold) searchParams.set('threshold', params.threshold.toString());
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());

  const query = searchParams.toString();
  return fetchAPI<InventoryResponse>(`/api/inventory${query ? `?${query}` : ''}`);
}

// =============================================================================
// BUY BOX
// =============================================================================

export interface GetBuyBoxParams {
  lost_only?: boolean;
}

export async function getBuyBox(params: GetBuyBoxParams = {}): Promise<BuyBoxResponse> {
  const searchParams = new URLSearchParams();

  if (params.lost_only) searchParams.set('lost_only', 'true');

  const query = searchParams.toString();
  return fetchAPI<BuyBoxResponse>(`/api/buy-box${query ? `?${query}` : ''}`);
}

// =============================================================================
// ALERTS
// =============================================================================

export interface GetAlertsParams {
  type?: AlertType;
  severity?: AlertSeverity;
  status?: AlertStatus;
  limit?: number;
  offset?: number;
}

export async function getAlerts(params: GetAlertsParams = {}): Promise<AlertsResponse> {
  const searchParams = new URLSearchParams();

  if (params.type) searchParams.set('type', params.type);
  if (params.severity) searchParams.set('severity', params.severity);
  if (params.status) searchParams.set('status', params.status);
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());

  const query = searchParams.toString();
  return fetchAPI<AlertsResponse>(`/api/alerts${query ? `?${query}` : ''}`);
}

export async function getAlertCounts(): Promise<AlertCounts> {
  return fetchAPI<AlertCounts>('/api/alerts/count');
}

export async function getAlert(id: string): Promise<Alert> {
  return fetchAPI<Alert>(`/api/alerts/${id}`);
}

export interface CreateAlertParams {
  type: AlertType;
  severity: AlertSeverity;
  marketplace: Marketplace;
  sku: string;
  message: string;
  title?: string;
  data?: Record<string, unknown>;
}

export async function createAlert(params: CreateAlertParams): Promise<Alert> {
  return fetchAPI<Alert>('/api/alerts', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function updateAlertStatus(id: string, status: AlertStatus): Promise<Alert> {
  return fetchAPI<Alert>(`/api/alerts/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

export async function dismissAlert(id: string): Promise<void> {
  await fetchAPI(`/api/alerts/${id}`, {
    method: 'DELETE',
  });
}

// =============================================================================
// HEALTH CHECK
// =============================================================================

export interface HealthStatus {
  status: string;
  version: string;
  timestamp: string;
  services?: Record<string, string>;
}

export async function getHealth(): Promise<HealthStatus> {
  // Health endpoint doesn't require auth
  const response = await fetch(`${API_URL}/health`);
  return response.json();
}
