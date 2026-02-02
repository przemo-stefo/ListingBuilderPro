// src/app/api/metrics/route.ts
// Purpose: Mock API endpoint returning seller performance metrics
// NOT for: Real metrics aggregation (replace with actual backend later)

import { NextResponse } from 'next/server';

const sellerMetrics = [
  {
    marketplace: 'amazon',
    feedback_score: 4.7,
    seller_rating: 98.2,
    return_rate: 3.1,
    defect_rate: 0.4,
    late_shipment_rate: 1.2,
    cancellation_rate: 0.8,
    order_count_30d: 1247,
    revenue_30d: 38420.50,
    last_updated: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
  },
  {
    marketplace: 'ebay',
    feedback_score: 4.9,
    seller_rating: 99.1,
    return_rate: 2.4,
    defect_rate: 0.2,
    late_shipment_rate: 0.8,
    cancellation_rate: 0.3,
    order_count_30d: 534,
    revenue_30d: 14890.25,
    last_updated: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
  },
  {
    marketplace: 'kaufland',
    feedback_score: 4.5,
    seller_rating: 96.8,
    return_rate: 4.2,
    defect_rate: 0.9,
    late_shipment_rate: 2.1,
    cancellation_rate: 1.5,
    order_count_30d: 312,
    revenue_30d: 9840.75,
    last_updated: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
  },
  {
    marketplace: 'allegro',
    feedback_score: 4.8,
    seller_rating: 97.5,
    return_rate: 2.8,
    defect_rate: 0.3,
    late_shipment_rate: 1.0,
    cancellation_rate: 0.5,
    order_count_30d: 189,
    revenue_30d: 6210.00,
    last_updated: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
];

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const marketplace = searchParams.get('marketplace');

  let filtered = sellerMetrics;
  if (marketplace) {
    filtered = filtered.filter(m => m.marketplace === marketplace);
  }

  const totalOrders = filtered.reduce((sum, m) => sum + m.order_count_30d, 0);
  const totalRevenue = filtered.reduce((sum, m) => sum + m.revenue_30d, 0);

  return NextResponse.json({
    metrics: filtered,
    total_orders_30d: totalOrders,
    total_revenue_30d: totalRevenue,
  });
}
