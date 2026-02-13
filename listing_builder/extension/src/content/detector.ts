// extension/src/content/detector.ts
// Purpose: Detect which marketplace the current page belongs to
// NOT for: Extracting product data (see extractors/)

import type { Marketplace } from "@shared/types";

interface DetectionResult {
  marketplace: Marketplace;
  isProductPage: boolean;
}

const PATTERNS: { marketplace: Marketplace; host: RegExp; path: RegExp }[] = [
  {
    marketplace: "amazon",
    host: /amazon\.(com|co\.uk|de|fr|it|es|pl)/,
    path: /\/(dp|gp\/product)\/[A-Z0-9]{10}/,
  },
  {
    marketplace: "allegro",
    host: /allegro\.pl/,
    path: /\/oferta\//,
  },
  {
    marketplace: "ebay",
    host: /ebay\.(com|co\.uk|de)/,
    path: /\/itm\//,
  },
  {
    marketplace: "kaufland",
    host: /kaufland\.de/,
    path: /\/product\//,
  },
];

export function detectMarketplace(url: string): DetectionResult | null {
  const parsed = new URL(url);

  for (const pattern of PATTERNS) {
    if (
      pattern.host.test(parsed.hostname) &&
      pattern.path.test(parsed.pathname)
    ) {
      return { marketplace: pattern.marketplace, isProductPage: true };
    }
  }

  // On marketplace domain but not a product page
  for (const pattern of PATTERNS) {
    if (pattern.host.test(parsed.hostname)) {
      return { marketplace: pattern.marketplace, isProductPage: false };
    }
  }

  return null;
}
