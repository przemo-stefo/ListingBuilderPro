// src/components/AlertsList.tsx
// Purpose: Display list of alerts with actions
// NOT for: API calls (parent handles data)

'use client';

import { cn, formatRelativeTime, truncate } from '@/lib/utils';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { SeverityBadge, StatusBadge, MarketplaceBadge } from '@/components/ui/badge';
import {
  AlertTriangle,
  ShoppingCart,
  Package,
  RotateCcw,
  Star,
  DollarSign,
  CheckCircle,
  XCircle,
  Eye
} from 'lucide-react';
import type { Alert } from '@/types';

interface AlertsListProps {
  alerts: Alert[];
  onAcknowledge?: (id: string) => void;
  onDismiss?: (id: string) => void;
  onView?: (id: string) => void;
  compact?: boolean;
}

// Get icon for alert type
function getAlertIcon(type: string) {
  const icons: Record<string, typeof AlertTriangle> = {
    buy_box_lost: ShoppingCart,
    low_stock: Package,
    returns_spike: RotateCcw,
    negative_review: Star,
    price_anomaly: DollarSign,
    listing_suppressed: AlertTriangle,
    policy_violation: AlertTriangle,
    competitor_price: DollarSign,
  };
  return icons[type] || AlertTriangle;
}

export function AlertsList({
  alerts,
  onAcknowledge,
  onDismiss,
  onView,
  compact = false
}: AlertsListProps) {
  if (alerts.length === 0) {
    return (
      <Card>
        <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
          <CheckCircle className="mb-2 h-8 w-8 text-green-500" />
          <p>No active alerts</p>
          <p className="text-sm">Your accounts are healthy</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert) => {
        const Icon = getAlertIcon(alert.type);

        return (
          <Card
            key={alert.id}
            hover
            className={cn(
              'transition-all',
              alert.severity === 'critical' && 'border-red-500/50',
              alert.severity === 'high' && 'border-orange-500/30'
            )}
          >
            <div className="flex items-start gap-4">
              {/* Icon */}
              <div className={cn(
                'rounded-lg p-2',
                alert.severity === 'critical' && 'bg-red-500/10 text-red-500',
                alert.severity === 'high' && 'bg-orange-500/10 text-orange-500',
                alert.severity === 'medium' && 'bg-yellow-500/10 text-yellow-500',
                alert.severity === 'low' && 'bg-blue-500/10 text-blue-500',
              )}>
                <Icon className="h-5 w-5" />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h4 className="font-medium text-white">
                    {compact ? truncate(alert.title, 40) : alert.title}
                  </h4>
                  <SeverityBadge severity={alert.severity} />
                  <StatusBadge status={alert.status} />
                  <MarketplaceBadge marketplace={alert.marketplace} />
                </div>

                {!compact && (
                  <p className="mt-1 text-sm text-muted-foreground">
                    {alert.message}
                  </p>
                )}

                <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
                  <span>SKU: {alert.sku}</span>
                  <span>{formatRelativeTime(alert.created_at)}</span>
                </div>
              </div>

              {/* Actions */}
              {(onAcknowledge || onDismiss || onView) && (
                <div className="flex items-center gap-1">
                  {onView && (
                    <button
                      onClick={() => onView(alert.id)}
                      className="p-2 text-muted-foreground hover:text-white transition-colors"
                      title="View details"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                  )}
                  {onAcknowledge && alert.status === 'active' && (
                    <button
                      onClick={() => onAcknowledge(alert.id)}
                      className="p-2 text-muted-foreground hover:text-yellow-500 transition-colors"
                      title="Acknowledge"
                    >
                      <CheckCircle className="h-4 w-4" />
                    </button>
                  )}
                  {onDismiss && (
                    <button
                      onClick={() => onDismiss(alert.id)}
                      className="p-2 text-muted-foreground hover:text-red-500 transition-colors"
                      title="Dismiss"
                    >
                      <XCircle className="h-4 w-4" />
                    </button>
                  )}
                </div>
              )}
            </div>
          </Card>
        );
      })}
    </div>
  );
}
