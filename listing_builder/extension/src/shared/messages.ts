// extension/src/shared/messages.ts
// Purpose: Message type constants for chrome.runtime messaging
// NOT for: API calls or storage

export const MSG = {
  PRODUCT_DETECTED: "PRODUCT_DETECTED",
  OPTIMIZE: "OPTIMIZE",
  TRACK_PRODUCT: "TRACK_PRODUCT",
  GET_PRODUCT: "GET_PRODUCT",
  GET_ALERTS: "GET_ALERTS",
  GET_TRACKED: "GET_TRACKED",
  GET_STATS: "GET_STATS",
  MARK_ALERT_READ: "MARK_ALERT_READ",
  OPEN_POPUP: "OPEN_POPUP",
} as const;

export type MessageType = (typeof MSG)[keyof typeof MSG];
