// extension/src/shared/storage.ts
// Purpose: chrome.storage.local wrapper for cached data
// NOT for: API calls or message passing

import type { ProductData, MonitorStats } from "./types";

const KEYS = {
  CURRENT_PRODUCT: "currentProduct",
  MONITOR_STATS: "monitorStats",
  OVERLAY_DISMISSED: "overlayDismissed",
} as const;

export async function setCurrentProduct(
  product: ProductData | null
): Promise<void> {
  await chrome.storage.local.set({ [KEYS.CURRENT_PRODUCT]: product });
}

export async function getCurrentProduct(): Promise<ProductData | null> {
  const result = await chrome.storage.local.get(KEYS.CURRENT_PRODUCT);
  return result[KEYS.CURRENT_PRODUCT] ?? null;
}

export async function setMonitorStats(stats: MonitorStats): Promise<void> {
  await chrome.storage.local.set({ [KEYS.MONITOR_STATS]: stats });
}

export async function getMonitorStats(): Promise<MonitorStats> {
  const result = await chrome.storage.local.get(KEYS.MONITOR_STATS);
  return (
    result[KEYS.MONITOR_STATS] ?? {
      tracked_count: 0,
      alerts_today: 0,
      unread_alerts: 0,
    }
  );
}

export async function isOverlayDismissed(url: string): Promise<boolean> {
  const result = await chrome.storage.local.get(KEYS.OVERLAY_DISMISSED);
  const dismissed: string[] = result[KEYS.OVERLAY_DISMISSED] ?? [];
  return dismissed.includes(url);
}

export async function dismissOverlay(url: string): Promise<void> {
  const result = await chrome.storage.local.get(KEYS.OVERLAY_DISMISSED);
  const dismissed: string[] = result[KEYS.OVERLAY_DISMISSED] ?? [];
  if (!dismissed.includes(url)) {
    dismissed.push(url);
    // Keep only last 100 dismissed URLs
    const trimmed = dismissed.slice(-100);
    await chrome.storage.local.set({ [KEYS.OVERLAY_DISMISSED]: trimmed });
  }
}
