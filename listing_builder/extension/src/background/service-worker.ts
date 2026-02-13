// extension/src/background/service-worker.ts
// Purpose: Background service worker — message routing, API proxy, alarms, badge
// NOT for: UI rendering or DOM access

import { MSG } from "@shared/messages";
import { setCurrentProduct, setMonitorStats } from "@shared/storage";
import * as api from "@shared/api";
import type { ProductData } from "@shared/types";

// --- Message routing ---

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  const { type, payload } = message;

  switch (type) {
    case MSG.PRODUCT_DETECTED:
      handleProductDetected(payload);
      break;

    case MSG.OPTIMIZE:
      handleOptimize(payload).then(sendResponse);
      return true; // async response

    case MSG.TRACK_PRODUCT:
      handleTrackProduct(payload).then(sendResponse);
      return true;

    case MSG.GET_ALERTS:
      api
        .getAlerts()
        .then((data) => sendResponse({ ok: true, data }))
        .catch((err) => sendResponse({ ok: false, error: err.message }));
      return true;

    case MSG.GET_TRACKED:
      api
        .getTrackedProducts()
        .then((data) => sendResponse({ ok: true, data }))
        .catch((err) => sendResponse({ ok: false, error: err.message }));
      return true;

    case MSG.GET_STATS:
      api
        .getMonitoringDashboard()
        .then((data) => sendResponse({ ok: true, data }))
        .catch((err) => sendResponse({ ok: false, error: err.message }));
      return true;

    case MSG.OPEN_POPUP:
      // MV3 can't open popup programmatically — store product for when user opens it
      if (payload) setCurrentProduct(payload);
      break;
  }
});

// --- Handlers ---

function handleProductDetected(product: ProductData) {
  setCurrentProduct(product);
}

async function handleOptimize(payload: {
  product_title: string;
  brand: string;
  keywords: { phrase: string; search_volume: number }[];
  marketplace?: string;
}) {
  try {
    const data = await api.optimize(payload);
    return { ok: true, data };
  } catch (err) {
    return { ok: false, error: (err as Error).message };
  }
}

async function handleTrackProduct(payload: {
  marketplace: string;
  product_id: string;
  product_name: string;
  url: string;
}) {
  try {
    const data = await api.trackProduct(payload);
    return { ok: true, data };
  } catch (err) {
    return { ok: false, error: (err as Error).message };
  }
}

// --- Alarms: check alerts every 30 min ---

chrome.alarms.create("checkAlerts", { periodInMinutes: 30 });

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name !== "checkAlerts") return;
  await refreshAlertBadge();
});

async function refreshAlertBadge() {
  try {
    const alerts = (await api.getAlerts(50)) as Array<{
      is_read?: boolean;
      severity?: string;
    }>;
    const unread = alerts.filter((a) => !a.is_read);
    const count = unread.length;

    // Update badge
    if (count > 0) {
      chrome.action.setBadgeText({ text: String(count) });
      // Red for high severity, yellow otherwise
      const hasHigh = unread.some((a) => a.severity === "high");
      chrome.action.setBadgeBackgroundColor({
        color: hasHigh ? "#EF4444" : "#F59E0B",
      });
    } else {
      chrome.action.setBadgeText({ text: "" });
    }

    // Cache stats
    setMonitorStats({
      tracked_count: 0, // Will be filled by dashboard call
      alerts_today: count,
      unread_alerts: count,
    });
  } catch {
    // Silent fail — alerts will refresh next cycle
  }
}

// Initial badge check on install/startup
chrome.runtime.onInstalled.addListener(() => {
  refreshAlertBadge();
});

chrome.runtime.onStartup.addListener(() => {
  refreshAlertBadge();
});
