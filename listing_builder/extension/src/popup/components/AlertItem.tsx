// extension/src/popup/components/AlertItem.tsx
// Purpose: Single alert row in Monitor tab
// NOT for: Optimizer results

import type { Alert } from "@shared/types";

const SEVERITY_COLORS: Record<string, string> = {
  high: "bg-red-900/50 text-red-400",
  medium: "bg-yellow-900/50 text-yellow-400",
  low: "bg-neutral-800 text-neutral-400",
};

const ALERT_TYPE_LABELS: Record<string, string> = {
  price_change: "Zmiana ceny",
  buy_box_lost: "Utrata Buy Box",
  low_stock: "Niski stan",
  listing_deactivated: "Dezaktywacja",
};

export default function AlertItem({ alert }: { alert: Alert }) {
  const timeAgo = formatTimeAgo(alert.created_at);
  const severityClass =
    SEVERITY_COLORS[alert.severity] ?? SEVERITY_COLORS.low;
  const typeLabel =
    ALERT_TYPE_LABELS[alert.alert_type] ?? alert.alert_type;

  return (
    <div
      className={`border border-dark-border rounded-lg p-2.5 ${
        alert.is_read ? "opacity-60" : ""
      }`}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className={`text-xs px-1.5 py-0.5 rounded ${severityClass}`}>
          {typeLabel}
        </span>
        <span className="text-xs text-neutral-600 ml-auto">{timeAgo}</span>
      </div>
      <p className="text-xs text-neutral-300 leading-relaxed">
        {alert.message}
      </p>
    </div>
  );
}

function formatTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 60) return `${mins}m temu`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h temu`;
  const days = Math.floor(hours / 24);
  return `${days}d temu`;
}
