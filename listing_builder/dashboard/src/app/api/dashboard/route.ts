// src/app/api/dashboard/route.ts
// Purpose: Mock API endpoint returning dashboard summary data
// NOT for: Real database queries (replace with actual backend later)

import { NextResponse } from 'next/server';

// Mock data that matches DashboardSummary type
const dashboardData = {
  health_score: 82,
  alerts: {
    total: 7,
    critical: 1,
    high: 2,
    medium: 3,
    low: 1,
    active: 5,
  },
  inventory: {
    total_skus: 234,
    total_units: 12_450,
    low_stock_count: 8,
    out_of_stock_count: 2,
    total_value: 187_320,
  },
  buy_box: {
    total_asins: 48,
    winning_count: 39,
    losing_count: 9,
    win_rate: 81.25,
  },
  marketplaces: [
    {
      marketplace: 'amazon',
      connected: true,
      inventory_count: 142,
      active_alerts: 3,
      health_score: 78,
    },
    {
      marketplace: 'ebay',
      connected: true,
      inventory_count: 56,
      active_alerts: 1,
      health_score: 88,
    },
    {
      marketplace: 'kaufland',
      connected: true,
      inventory_count: 36,
      active_alerts: 1,
      health_score: 85,
    },
  ],
  last_updated: new Date().toISOString(),
};

export async function GET() {
  return NextResponse.json(dashboardData);
}
