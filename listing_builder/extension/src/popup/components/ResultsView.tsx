// extension/src/popup/components/ResultsView.tsx
// Purpose: Display optimization results with copy buttons
// NOT for: Product detection or API calls

import { useState } from "react";
import type { OptimizationResult } from "@shared/types";

export default function ResultsView({
  result,
}: {
  result: OptimizationResult;
}) {
  return (
    <div className="space-y-3">
      {/* Ranking Juice score */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-neutral-500">Ranking Juice:</span>
        <span
          className={`text-sm font-bold ${
            result.ranking_juice >= 75
              ? "text-emerald-400"
              : result.ranking_juice >= 50
              ? "text-yellow-400"
              : "text-red-400"
          }`}
        >
          {result.ranking_juice}/100
        </span>
      </div>

      <CopyField label="Tytuł" value={result.title} />

      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-neutral-500">Bullet Points</span>
          <CopyButton
            text={result.bullets.map((b, i) => `${i + 1}. ${b}`).join("\n")}
          />
        </div>
        <ul className="space-y-1">
          {result.bullets.map((bullet, i) => (
            <li
              key={i}
              className="text-xs text-neutral-300 bg-dark-secondary border border-dark-border rounded px-2 py-1.5"
            >
              {bullet}
            </li>
          ))}
        </ul>
      </div>

      <CopyField label="Opis" value={result.description} multiline />
      <CopyField label="Backend Keywords" value={result.backend_keywords} />
    </div>
  );
}

function CopyField({
  label,
  value,
  multiline,
}: {
  label: string;
  value: string;
  multiline?: boolean;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-neutral-500">{label}</span>
        <CopyButton text={value} />
      </div>
      <div
        className={`text-xs text-neutral-300 bg-dark-secondary border border-dark-border rounded px-2 py-1.5 ${
          multiline ? "max-h-24 overflow-y-auto" : "truncate"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Fallback for clipboard API failure
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="text-xs px-2 py-0.5 rounded bg-dark-border text-neutral-400 hover:text-white transition-colors"
    >
      {copied ? "Skopiowano!" : "Kopiuj"}
    </button>
  );
}
