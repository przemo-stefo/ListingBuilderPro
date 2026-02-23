// extension/src/popup/App.tsx
// Purpose: Main popup shell with 2 tabs: Optimizer | Monitor
// NOT for: Content scripts or background logic

import { useState } from "react";
import OptimizerTab from "./tabs/OptimizerTab";
import MonitorTab from "./tabs/MonitorTab";

type Tab = "optimizer" | "monitor";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("optimizer");

  return (
    <div className="w-popup h-popup bg-dark-primary text-white flex flex-col">
      {/* Header */}
      <div className="px-4 pt-3 pb-2 border-b border-dark-border">
        <h1 className="text-base font-bold tracking-tight">
          Niezbędnik Sprzedawcy
        </h1>
        <p className="text-xs text-neutral-500 mt-0.5">
          Optymalizacja &amp; Monitoring
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-dark-border">
        <TabButton
          label="Optimizer"
          active={activeTab === "optimizer"}
          onClick={() => setActiveTab("optimizer")}
        />
        <TabButton
          label="Monitor"
          active={activeTab === "monitor"}
          onClick={() => setActiveTab("monitor")}
        />
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === "optimizer" ? <OptimizerTab /> : <MonitorTab />}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-dark-border text-center">
        <a
          href="https://panel.octohelper.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-emerald-500 hover:text-emerald-400"
        >
          Otwórz pełny panel →
        </a>
      </div>
    </div>
  );
}

function TabButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 py-2.5 text-sm font-medium transition-colors ${
        active
          ? "text-emerald-400 border-b-2 border-emerald-400"
          : "text-neutral-500 hover:text-neutral-300"
      }`}
    >
      {label}
    </button>
  );
}
