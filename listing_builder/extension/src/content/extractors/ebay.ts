// extension/src/content/extractors/ebay.ts
// Purpose: Extract product data from eBay item pages
// NOT for: Other marketplaces

import type { ProductData } from "@shared/types";

export function extractEbay(): ProductData | null {
  // Item ID from URL: /itm/XXXXXXXXXXXXX or /itm/title/XXXXXXXXXXXXX
  const idMatch = window.location.pathname.match(/\/itm\/(?:.*?\/)?(\d+)/);
  const productId = idMatch?.[1] ?? "";
  if (!productId) return null;

  // Title
  const titleEl =
    document.querySelector("#itemTitle") ??
    document.querySelector("h1.x-item-title__mainTitle span");
  let title = titleEl?.textContent?.trim() ?? "";
  // Remove "Details about " prefix that eBay sometimes adds
  title = title.replace(/^Details about\s+/i, "");

  // Price — eBay 2025+ uses ux-textspans inside price section
  let price = "";
  const priceEl =
    document.querySelector("#prcIsum") ??
    document.querySelector(".x-price-primary span.ux-textspans") ??
    document.querySelector('[itemprop="price"]');
  if (priceEl) {
    price = priceEl.textContent?.trim() ?? "";
    // WHY: eBay sometimes duplicates price text (e.g. "US $24.14US $24.14")
    const half = Math.floor(price.length / 2);
    if (price.length > 6 && price.slice(0, half) === price.slice(half)) {
      price = price.slice(0, half);
    }
  }
  // WHY: Fallback for ended listings or different layouts — scan for currency pattern
  if (!price) {
    for (const el of document.querySelectorAll("span, div")) {
      const t = el.textContent?.trim() ?? "";
      if (/^(US\s*\$|EUR|£|PLN)\s*[\d,.]+$/.test(t) && t.length < 25) {
        price = t;
        break;
      }
    }
  }

  // Brand — from item specifics table
  let brand = "";
  const specCols = document.querySelectorAll(".ux-layout-section-evo__col");
  specCols.forEach((col) => {
    const lbl = col.querySelector(".ux-labels-values__labels");
    const val = col.querySelector(".ux-labels-values__values");
    if (lbl && val && /brand/i.test(lbl.textContent ?? "")) {
      brand = val.textContent?.trim() ?? "";
    }
  });

  return {
    marketplace: "ebay",
    productId,
    title,
    price,
    brand,
    url: window.location.href,
  };
}
