// extension/src/content/extractors/kaufland.ts
// Purpose: Extract product data from Kaufland.de product pages
// NOT for: Other marketplaces

import type { ProductData } from "@shared/types";

export function extractKaufland(): ProductData | null {
  // Product ID from URL: /product/XXXXXXXXX
  const idMatch = window.location.pathname.match(/\/product\/(\d+)/);
  const productId = idMatch?.[1] ?? "";
  if (!productId) return null;

  // Title
  const titleEl = document.querySelector("h1");
  const title = titleEl?.textContent?.trim() ?? "";

  // Price
  const priceEl =
    document.querySelector('[data-t="currentPrice"]') ??
    document.querySelector(".product-price") ??
    document.querySelector(".rd-price");
  const price = priceEl?.textContent?.trim() ?? "";

  // Brand
  const brandEl = document.querySelector(".rd-brand-name, .product-brand");
  const brand = brandEl?.textContent?.trim() ?? "";

  return {
    marketplace: "kaufland",
    productId,
    title,
    price,
    brand,
    url: window.location.href,
  };
}
