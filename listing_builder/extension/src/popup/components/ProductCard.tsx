// extension/src/popup/components/ProductCard.tsx
// Purpose: Display detected product info (marketplace, title, brand, ID)
// NOT for: Optimization results

import type { ProductData } from "@shared/types";

const MARKETPLACE_LABELS: Record<string, string> = {
  amazon: "Amazon",
  allegro: "Allegro",
  ebay: "eBay",
  kaufland: "Kaufland",
};

export default function ProductCard({ product }: { product: ProductData }) {
  return (
    <div className="bg-dark-secondary border border-dark-border rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs px-2 py-0.5 bg-emerald-900/50 text-emerald-400 rounded font-medium">
          {MARKETPLACE_LABELS[product.marketplace] ?? product.marketplace}
        </span>
        <span className="text-xs text-neutral-500 font-mono">
          {product.productId}
        </span>
      </div>

      <h3 className="text-sm font-medium leading-snug line-clamp-2 mb-1">
        {product.title || "Brak tytułu"}
      </h3>

      <div className="flex items-center gap-3 text-xs text-neutral-400">
        {product.brand && <span>Marka: {product.brand}</span>}
        {product.price && <span>Cena: {product.price}</span>}
      </div>
    </div>
  );
}
