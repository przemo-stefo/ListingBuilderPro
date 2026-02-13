// extension/src/content/extractors/amazon.ts
// Purpose: Extract product data from Amazon product pages
// NOT for: Other marketplaces

import type { ProductData } from "@shared/types";

export function extractAmazon(): ProductData | null {
  // ASIN from URL (/dp/BXXXXXXXXX or /gp/product/BXXXXXXXXX)
  const asinMatch = window.location.pathname.match(
    /\/(?:dp|gp\/product)\/([A-Z0-9]{10})/
  );
  if (!asinMatch) return null;

  const asin = asinMatch[1];

  // Title
  const titleEl = document.querySelector("#productTitle");
  const title = titleEl?.textContent?.trim() ?? "";

  // Price — try multiple selectors (Amazon varies by region)
  const priceEl =
    document.querySelector(".a-price .a-offscreen") ??
    document.querySelector("#priceblock_ourprice") ??
    document.querySelector("#priceblock_dealprice") ??
    document.querySelector(".a-price-whole");
  const price = priceEl?.textContent?.trim() ?? "";

  // Brand
  const brandEl =
    document.querySelector("#bylineInfo") ??
    document.querySelector('a[id="bylineInfo"]');
  let brand = brandEl?.textContent?.trim() ?? "";
  // Clean "Visit the X Store" / "Brand: X"
  brand = brand.replace(/^(Visit the |Brand:\s*)/i, "").replace(/\s*Store$/, "");

  // Image
  const imgEl = document.querySelector("#landingImage") as HTMLImageElement;
  const imageUrl = imgEl?.src ?? undefined;

  return {
    marketplace: "amazon",
    productId: asin,
    title,
    price,
    brand,
    url: window.location.href,
    imageUrl,
  };
}
