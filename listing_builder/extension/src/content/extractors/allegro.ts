// extension/src/content/extractors/allegro.ts
// Purpose: Extract product data from Allegro offer pages
// NOT for: Other marketplaces

import type { ProductData } from "@shared/types";

export function extractAllegro(): ProductData | null {
  // Product ID from URL: /oferta/product-name-XXXXXXXXXX
  const idMatch = window.location.pathname.match(/\/oferta\/.*?-(\d+)$/);
  // Fallback: grab last numeric segment
  const fallbackMatch = window.location.pathname.match(/(\d{8,})$/);
  const productId = idMatch?.[1] ?? fallbackMatch?.[1] ?? "";
  if (!productId) return null;

  // Title
  const titleEl = document.querySelector("h1");
  const title = titleEl?.textContent?.trim() ?? "";

  // Price — Allegro uses data-testid attributes
  const priceEl = document.querySelector('[data-testid="price"]');
  const price = priceEl?.textContent?.trim() ?? "";

  // Seller/brand — best effort
  const sellerEl = document.querySelector('[data-testid="seller-info"] a');
  const brand = sellerEl?.textContent?.trim() ?? "";

  return {
    marketplace: "allegro",
    productId,
    title,
    price,
    brand,
    url: window.location.href,
  };
}
