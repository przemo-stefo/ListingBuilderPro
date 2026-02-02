// src/app/dashboard/alerts/page.tsx
// Purpose: Full alerts management page with filtering and actions
// NOT for: Alert definitions or API logic (see /lib/api.ts and /types)

'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { AlertsList } from '@/components/AlertsList';
import { getAlerts, updateAlertStatus, dismissAlert } from '@/lib/api';
import type { Alert, AlertSeverity, AlertStatus } from '@/types';
import {
  Bell,
  AlertTriangle,
  RefreshCw,
  ShieldAlert,
  ArrowUpCircle,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

type SeverityFilter = AlertSeverity | 'all';
type StatusFilter = AlertStatus | 'all';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

  useEffect(() => {
    fetchAlerts();
  }, [severityFilter, statusFilter]);

  async function fetchAlerts() {
    setLoading(true);
    setError(null);

    try {
      const params: Record<string, string> = {};
      if (severityFilter !== 'all') params.severity = severityFilter;
      if (statusFilter !== 'all') params.status = statusFilter;

      const data = await getAlerts(params);
      setAlerts(data.alerts);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  }

  async function handleAcknowledge(id: string) {
    try {
      await updateAlertStatus(id, 'acknowledged');
      // Optimistic update — change status locally
      setAlerts(prev =>
        prev.map(a => (a.id === id ? { ...a, status: 'acknowledged' as AlertStatus } : a))
      );
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  }

  async function handleDismiss(id: string) {
    try {
      await dismissAlert(id);
      // Remove from list
      setAlerts(prev => prev.filter(a => a.id !== id));
    } catch (err) {
      console.error('Failed to dismiss alert:', err);
    }
  }

  // Summary counts derived from current alert list
  const counts = {
    total: alerts.length,
    critical: alerts.filter(a => a.severity === 'critical').length,
    high: alerts.filter(a => a.severity === 'high').length,
    medium: alerts.filter(a => a.severity === 'medium').length,
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="border-red-500/30 bg-red-500/5">
        <div className="flex flex-col items-center justify-center py-8">
          <AlertTriangle className="mb-2 h-8 w-8 text-red-500" />
          <p className="text-red-500">{error}</p>
          <button
            onClick={fetchAlerts}
            className="mt-4 rounded-lg bg-red-500/10 px-4 py-2 text-sm text-red-500 hover:bg-red-500/20"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Alerts</h1>
          <p className="text-muted-foreground">
            Monitor and manage compliance alerts across all marketplaces
          </p>
        </div>
        <button
          onClick={fetchAlerts}
          className="flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2 text-sm hover:bg-muted transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-blue-500/10 p-2">
              <Bell className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{counts.total}</p>
              <p className="text-xs text-muted-foreground">Total</p>
            </div>
          </CardContent>
        </Card>
        <Card className={cn(counts.critical > 0 && 'border-red-500/30')}>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-red-500/10 p-2">
              <ShieldAlert className="h-5 w-5 text-red-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-red-500">{counts.critical}</p>
              <p className="text-xs text-muted-foreground">Critical</p>
            </div>
          </CardContent>
        </Card>
        <Card className={cn(counts.high > 0 && 'border-orange-500/30')}>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-orange-500/10 p-2">
              <ArrowUpCircle className="h-5 w-5 text-orange-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-orange-500">{counts.high}</p>
              <p className="text-xs text-muted-foreground">High</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-4">
            <div className="rounded-lg bg-yellow-500/10 p-2">
              <AlertCircle className="h-5 w-5 text-yellow-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-500">{counts.medium}</p>
              <p className="text-xs text-muted-foreground">Medium</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">Severity</label>
          <select
            value={severityFilter}
            onChange={e => setSeverityFilter(e.target.value as SeverityFilter)}
            className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-green-500"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">Status</label>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value as StatusFilter)}
            className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-green-500"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>
        </div>
      </div>

      {/* Alert List — full mode (not compact) */}
      <AlertsList
        alerts={alerts}
        onAcknowledge={handleAcknowledge}
        onDismiss={handleDismiss}
      />
    </div>
  );
}
