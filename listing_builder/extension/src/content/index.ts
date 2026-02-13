// extension/src/content/index.ts
// Purpose: Content script entry — detect marketplace, extract data, inject overlay
// NOT for: API calls (those go through service worker)

import { detectMarketplace } from "./detector";
import { extractAmazon } from "./extractors/amazon";
import { extractAllegro } from "./extractors/allegro";
import { extractEbay } from "./extractors/ebay";
import { extractKaufland } from "./extractors/kaufland";
import { injectOverlay } from "./overlay";
import { MSG } from "@shared/messages";
import type { ProductData, Marketplace } from "@shared/types";

const EXTRACTORS: Record<Marketplace, () => ProductData | null> = {
  amazon: extractAmazon,
  allegro: extractAllegro,
  ebay: extractEbay,
  kaufland: extractKaufland,
};

function run() {
  const detection = detectMarketplace(window.location.href);
  if (!detection?.isProductPage) return;

  const extractor = EXTRACTORS[detection.marketplace];
  const product = extractor();
  if (!product) return;

  // Notify service worker about detected product
  chrome.runtime.sendMessage({
    type: MSG.PRODUCT_DETECTED,
    payload: product,
  });

  // Inject floating overlay button
  injectOverlay(product);
}

// Run after page is loaded
run();

// Re-run on SPA navigation (Amazon uses pushState)
let lastUrl = window.location.href;
const observer = new MutationObserver(() => {
  if (window.location.href !== lastUrl) {
    lastUrl = window.location.href;
    // Small delay for DOM to update after SPA navigation
    setTimeout(run, 1000);
  }
});

observer.observe(document.body, { childList: true, subtree: true });
