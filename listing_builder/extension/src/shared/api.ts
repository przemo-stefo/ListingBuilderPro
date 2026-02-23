// extension/src/shared/api.ts
// Purpose: API client — all calls go through Vercel proxy (API key injected server-side)
// NOT for: Direct backend calls

const BASE_URL = "https://panel.octohelper.com/api/proxy";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}/${path.replace(/^\//, "")}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${text}`);
  }

  return res.json();
}

// --- Optimizer ---

export interface OptimizePayload {
  product_title: string;
  brand: string;
  keywords: { phrase: string; search_volume: number }[];
  marketplace?: string;
}

export function optimize(payload: OptimizePayload) {
  return request<Record<string, unknown>>("optimizer/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// --- Monitoring ---

export function getAlerts(limit = 20) {
  return request<Record<string, unknown>[]>(
    `monitoring/alerts?limit=${limit}`
  );
}

export function getTrackedProducts() {
  return request<Record<string, unknown>[]>("monitoring/tracked");
}

export function trackProduct(payload: {
  marketplace: string;
  product_id: string;
  product_name: string;
  url: string;
}) {
  return request<Record<string, unknown>>("monitoring/tracked", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getMonitoringDashboard() {
  return request<Record<string, unknown>>("monitoring/dashboard");
}
