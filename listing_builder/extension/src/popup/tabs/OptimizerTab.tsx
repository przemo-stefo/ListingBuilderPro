// extension/src/popup/tabs/OptimizerTab.tsx
// Purpose: Optimizer tab — detect product, optimize, show results
// NOT for: Monitoring or alerts

import { useState, useEffect } from "react";
import { getCurrentProduct } from "@shared/storage";
import { MSG } from "@shared/messages";
import type { ProductData, OptimizationResult } from "@shared/types";
import ProductCard from "../components/ProductCard";
import ResultsView from "../components/ResultsView";

type Status = "idle" | "loading" | "done" | "error";

export default function OptimizerTab() {
  const [product, setProduct] = useState<ProductData | null>(null);
  const [keywords, setKeywords] = useState("");
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState("");

  // Load detected product from storage on mount
  useEffect(() => {
    getCurrentProduct().then((p) => {
      if (p) setProduct(p);
    });
  }, []);

  const handleOptimize = () => {
    if (!product) return;

    setStatus("loading");
    setError("");
    setResult(null);

    const keywordList = keywords
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean);

    chrome.runtime.sendMessage(
      {
        type: MSG.OPTIMIZE,
        payload: {
          product_title: product.title,
          brand: product.brand || "Generic",
          // WHY: Backend expects {phrase, search_volume} objects, not plain strings
          keywords: keywordList.length > 0
            ? keywordList.map((k) => ({ phrase: k, search_volume: 0 }))
            : [{ phrase: product.title.split(" ").slice(0, 3).join(" "), search_volume: 0 }],
          marketplace: product.marketplace,
        },
      },
      (response) => {
        if (response?.ok) {
          const data = response.data;
          // WHY: Backend nests results under "listing" key
          const listing = data.listing ?? {};
          const rj = data.ranking_juice ?? {};
          setResult({
            title: listing.title ?? "",
            bullets: listing.bullet_points ?? [],
            description: listing.description ?? "",
            backend_keywords: listing.backend_keywords ?? "",
            ranking_juice: rj.score ?? 0,
            trace: data.trace,
            listing_history_id: data.listing_history_id,
          });
          setStatus("done");
        } else {
          setError(response?.error ?? "Nieznany błąd");
          setStatus("error");
        }
      }
    );
  };

  // No product detected
  if (!product) {
    return (
      <div className="p-4 text-center">
        <div className="text-neutral-500 text-sm mt-8">
          <p className="text-2xl mb-3">🔍</p>
          <p>Otwórz stronę produktu na:</p>
          <p className="text-neutral-400 mt-1">
            Amazon, Allegro, eBay lub Kaufland
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-3">
      <ProductCard product={product} />

      {/* Keywords input */}
      <div>
        <label className="text-xs text-neutral-500 block mb-1">
          Słowa kluczowe (opcjonalne, rozdziel przecinkami)
        </label>
        <input
          type="text"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          placeholder="np. garlic press, kitchen tool, stainless steel"
          className="w-full bg-dark-secondary border border-dark-border rounded px-3 py-2 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-emerald-600"
        />
      </div>

      {/* Optimize button */}
      <button
        onClick={handleOptimize}
        disabled={status === "loading"}
        className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:bg-neutral-700 disabled:text-neutral-500 text-white text-sm font-medium transition-colors"
      >
        {status === "loading" ? (
          <span className="flex items-center justify-center gap-2">
            <Spinner /> Optymalizuję...
          </span>
        ) : (
          "Optymalizuj listing"
        )}
      </button>

      {/* Error */}
      {status === "error" && (
        <div className="text-xs text-red-400 bg-red-900/20 border border-red-900 rounded p-2">
          {error}
        </div>
      )}

      {/* Results */}
      {result && <ResultsView result={result} />}
    </div>
  );
}

function Spinner() {
  return (
    <svg
      className="animate-spin h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}
