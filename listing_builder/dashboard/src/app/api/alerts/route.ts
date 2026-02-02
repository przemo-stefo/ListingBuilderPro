// src/app/api/alerts/route.ts
// Purpose: Mock API endpoint returning alerts data
// NOT for: Real alert processing (replace with actual backend later)

import { NextResponse } from 'next/server';

const alerts = [
  {
    id: 'alert-001',
    type: 'listing_suppressed',
    severity: 'critical',
    status: 'active',
    marketplace: 'amazon',
    sku: 'DE-EPR-1042',
    title: 'Listing Suppressed - Missing EPR Registration',
    message: 'Amazon DE has suppressed your listing due to missing EPR packaging registration. Register at LUCID within 48 hours to restore.',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'alert-002',
    type: 'buy_box_lost',
    severity: 'high',
    status: 'active',
    marketplace: 'amazon',
    sku: 'UK-BB-3391',
    title: 'Buy Box Lost - Price Undercut',
    message: 'Competitor undercut your price by 8%. Current Buy Box price is $24.99, your price is $27.15.',
    created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    data: { your_price: 27.15, buy_box_price: 24.99 },
  },
  {
    id: 'alert-003',
    type: 'policy_violation',
    severity: 'high',
    status: 'active',
    marketplace: 'kaufland',
    sku: 'KL-WEEE-0087',
    title: 'WEEE Registration Expiring',
    message: 'Your WEEE registration for Kaufland DE expires in 14 days. Renew to avoid listing removal.',
    created_at: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'alert-004',
    type: 'low_stock',
    severity: 'medium',
    status: 'active',
    marketplace: 'amazon',
    sku: 'FR-INV-2210',
    title: 'Low Stock Warning',
    message: 'Only 12 units remaining. Based on current velocity, stock will run out in 5 days.',
    created_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'alert-005',
    type: 'price_anomaly',
    severity: 'medium',
    status: 'active',
    marketplace: 'ebay',
    sku: 'EB-PRC-0553',
    title: 'Price Drop Detected',
    message: 'Market price for this product dropped 15% in the last 24 hours across 3 competitors.',
    created_at: new Date(Date.now() - 18 * 60 * 60 * 1000).toISOString(),
  },
];

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const severity = searchParams.get('severity');
  const status = searchParams.get('status');

  let filtered = alerts;
  if (severity) filtered = filtered.filter(a => a.severity === severity);
  if (status) filtered = filtered.filter(a => a.status === status);

  return NextResponse.json({
    alerts: filtered,
    total: filtered.length,
    limit: 10,
    offset: 0,
  });
}
