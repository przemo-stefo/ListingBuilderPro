// src/app/page.tsx
// Purpose: Main dashboard page
// NOT for: Component definitions (see /components)

'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { HealthScore } from '@/components/HealthScore';
import { StatCard } from '@/components/StatCard';
import { AlertsList } from '@/components/AlertsList';
import { MarketplaceBadge } from '@/components/ui/badge';
import { formatCurrency, formatNumber, formatPercent, cn } from '@/lib/utils';
import {
  getDashboard,
  getAlerts,
  updateAlertStatus,
  dismissAlert
} from '@/lib/api';
import type { DashboardSummary, Alert } from '@/types';
import {
  Bell,
  Package,
  ShoppingCart,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
  TrendingDown
} from 'lucide-react';

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data on mount
  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    setError(null);

    try {
      const [dashboardData, alertsData] = await Promise.all([
        getDashboard(),
        getAlerts({ status: 'active', limit: 5 }),
      ]);

      setDashboard(dashboardData);
      setAlerts(alertsData.alerts);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }

  async function handleAcknowledge(id: string) {
    try {
      await updateAlertStatus(id, 'acknowledged');
      setAlerts(alerts.map(a =>
        a.id === id ? { ...a, status: 'acknowledged' } : a
      ));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  }

  async function handleDismiss(id: string) {
    try {
      await dismissAlert(id);
      setAlerts(alerts.filter(a => a.id !== id));
    } catch (err) {
      console.error('Failed to dismiss alert:', err);
    }
  }

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-500/30 bg-red-500/5">
        <div className="flex flex-col items-center justify-center py-8">
          <AlertTriangle className="mb-2 h-8 w-8 text-red-500" />
          <p className="text-red-500">{error}</p>
          <button
            onClick={fetchData}
            className="mt-4 rounded-lg bg-red-500/10 px-4 py-2 text-sm text-red-500 hover:bg-red-500/20"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  if (!dashboard) return null;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor your marketplace accounts
          </p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2 text-sm hover:bg-muted transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Health Score & Stats */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
        {/* Health Score Card */}
        <Card className="md:col-span-1">
          <CardContent className="flex items-center justify-center py-4">
            <HealthScore score={dashboard.health_score} />
          </CardContent>
        </Card>

        {/* Stats */}
        <div className="md:col-span-3 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard
            title="Active Alerts"
            value={dashboard.alerts.total}
            subtitle={`${dashboard.alerts.critical} critical`}
            icon={Bell}
            variant={dashboard.alerts.critical > 0 ? 'danger' : 'default'}
          />
          <StatCard
            title="Total SKUs"
            value={formatNumber(dashboard.inventory.total_skus)}
            subtitle={`${dashboard.inventory.low_stock_count} low stock`}
            icon={Package}
            variant={dashboard.inventory.low_stock_count > 5 ? 'warning' : 'default'}
          />
          <StatCard
            title="Buy Box Win Rate"
            value={formatPercent(dashboard.buy_box.win_rate)}
            subtitle={`${dashboard.buy_box.winning_count}/${dashboard.buy_box.total_asins} ASINs`}
            icon={ShoppingCart}
            trend={dashboard.buy_box.win_rate >= 80 ? 'up' : 'down'}
            variant={dashboard.buy_box.win_rate < 50 ? 'danger' : 'default'}
          />
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Alerts */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-red-500" />
                Recent Alerts
              </CardTitle>
              <a
                href="/alerts"
                className="text-sm text-muted-foreground hover:text-white"
              >
                View all →
              </a>
            </CardHeader>
            <CardContent>
              <AlertsList
                alerts={alerts}
                onAcknowledge={handleAcknowledge}
                onDismiss={handleDismiss}
                compact
              />
            </CardContent>
          </Card>
        </div>

        {/* Marketplaces */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Marketplaces</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {dashboard.marketplaces.map((mp) => (
                  <div
                    key={mp.marketplace}
                    className="flex items-center justify-between rounded-lg border border-border-secondary p-3"
                  >
                    <div className="flex items-center gap-3">
                      <MarketplaceBadge marketplace={mp.marketplace} />
                      <div>
                        <p className="text-sm font-medium text-white capitalize">
                          {mp.marketplace}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {mp.inventory_count} products
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={cn(
                        'text-lg font-bold',
                        mp.health_score >= 80 ? 'text-green-500' :
                        mp.health_score >= 60 ? 'text-lime-500' :
                        mp.health_score >= 40 ? 'text-yellow-500' : 'text-red-500'
                      )}>
                        {mp.health_score}
                      </p>
                      {mp.active_alerts > 0 && (
                        <p className="text-xs text-red-400">
                          {mp.active_alerts} alerts
                        </p>
                      )}
                    </div>
                  </div>
                ))}

                {dashboard.marketplaces.length === 0 && (
                  <p className="py-4 text-center text-muted-foreground">
                    No marketplaces connected
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Inventory Summary */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Inventory Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Value</span>
                  <span className="font-medium text-white">
                    {formatCurrency(dashboard.inventory.total_value)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Units</span>
                  <span className="font-medium text-white">
                    {formatNumber(dashboard.inventory.total_units)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Out of Stock</span>
                  <span className={cn(
                    'font-medium',
                    dashboard.inventory.out_of_stock_count > 0 ? 'text-red-500' : 'text-green-500'
                  )}>
                    {dashboard.inventory.out_of_stock_count}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
