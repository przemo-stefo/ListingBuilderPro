// extension/src/popup/tabs/MonitorTab.tsx
// Purpose: Monitor tab — tracked products, alerts, track button
// NOT for: Optimizer logic

import { useState, useEffect } from "react";
import { getCurrentProduct } from "@shared/storage";
import { MSG } from "@shared/messages";
import type { ProductData, Alert, TrackedProduct } from "@shared/types";
import AlertItem from "../components/AlertItem";

type View = "alerts" | "tracked";

export default function MonitorTab() {
  const [product, setProduct] = useState<ProductData | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [tracked, setTracked] = useState<TrackedProduct[]>([]);
  const [view, setView] = useState<View>("alerts");
  const [loading, setLoading] = useState(true);
  const [tracking, setTracking] = useState(false);

  useEffect(() => {
    getCurrentProduct().then(setProduct);
    loadData();
  }, []);

  function loadData() {
    setLoading(true);
    Promise.all([
      sendMessage(MSG.GET_ALERTS),
      sendMessage(MSG.GET_TRACKED),
    ]).then(([alertsRes, trackedRes]) => {
      if (alertsRes?.ok) setAlerts(alertsRes.data as Alert[]);
      if (trackedRes?.ok) setTracked(trackedRes.data as TrackedProduct[]);
      setLoading(false);
    });
  }

  const handleTrack = () => {
    if (!product) return;
    setTracking(true);

    sendMessage(MSG.TRACK_PRODUCT, {
      marketplace: product.marketplace,
      product_id: product.productId,
      product_name: product.title,
      url: product.url,
    }).then((res) => {
      setTracking(false);
      if (res?.ok) loadData();
    });
  };

  const isAlreadyTracked = tracked.some(
    (t) => t.product_id === product?.productId
  );

  return (
    <div className="p-3 space-y-3">
      {/* Stats bar */}
      <div className="flex gap-2">
        <StatBox label="Śledzonych" value={tracked.length} />
        <StatBox label="Alertów" value={alerts.length} />
      </div>

      {/* Track button — only if on a product page */}
      {product && !isAlreadyTracked && (
        <button
          onClick={handleTrack}
          disabled={tracking}
          className="w-full py-2 rounded-lg bg-dark-secondary border border-dark-border hover:border-emerald-600 text-sm text-neutral-300 hover:text-white transition-colors disabled:opacity-50"
        >
          {tracking ? "Dodaję..." : `Śledź: ${truncate(product.title, 40)}`}
        </button>
      )}

      {product && isAlreadyTracked && (
        <div className="text-xs text-emerald-500 text-center py-1">
          Ten produkt jest już śledzony
        </div>
      )}

      {/* View toggle */}
      <div className="flex gap-1 bg-dark-secondary rounded-lg p-0.5">
        <ToggleButton
          label={`Alerty (${alerts.length})`}
          active={view === "alerts"}
          onClick={() => setView("alerts")}
        />
        <ToggleButton
          label={`Śledzone (${tracked.length})`}
          active={view === "tracked"}
          onClick={() => setView("tracked")}
        />
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center text-neutral-500 text-sm py-6">
          Ładowanie...
        </div>
      ) : view === "alerts" ? (
        <AlertList alerts={alerts} />
      ) : (
        <TrackedList tracked={tracked} />
      )}
    </div>
  );
}

function AlertList({ alerts }: { alerts: Alert[] }) {
  if (alerts.length === 0) {
    return (
      <div className="text-center text-neutral-500 text-sm py-6">
        Brak alertów
      </div>
    );
  }
  return (
    <div className="space-y-2">
      {alerts.map((a) => (
        <AlertItem key={a.id} alert={a} />
      ))}
    </div>
  );
}

function TrackedList({ tracked }: { tracked: TrackedProduct[] }) {
  if (tracked.length === 0) {
    return (
      <div className="text-center text-neutral-500 text-sm py-6">
        Brak śledzonych produktów
      </div>
    );
  }
  return (
    <div className="space-y-2">
      {tracked.map((t) => (
        <div
          key={t.id}
          className="bg-dark-secondary border border-dark-border rounded-lg p-2.5"
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs px-1.5 py-0.5 bg-neutral-800 text-neutral-400 rounded">
              {t.marketplace}
            </span>
            {t.current_price != null && (
              <span className="text-xs text-neutral-500 ml-auto">
                {t.current_price}
              </span>
            )}
          </div>
          <p className="text-xs text-neutral-300 line-clamp-1">
            {t.product_name}
          </p>
        </div>
      ))}
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex-1 bg-dark-secondary border border-dark-border rounded-lg p-2.5 text-center">
      <div className="text-lg font-bold text-white">{value}</div>
      <div className="text-xs text-neutral-500">{label}</div>
    </div>
  );
}

function ToggleButton({
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
      className={`flex-1 py-1.5 text-xs rounded-md transition-colors ${
        active
          ? "bg-dark-border text-white"
          : "text-neutral-500 hover:text-neutral-300"
      }`}
    >
      {label}
    </button>
  );
}

function sendMessage(type: string, payload?: unknown): Promise<any> {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ type, payload }, resolve);
  });
}

function truncate(str: string, max: number): string {
  return str.length > max ? str.slice(0, max) + "..." : str;
}
