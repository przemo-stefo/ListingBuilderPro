// frontend/src/app/api/analytics/route.ts
// Purpose: Mock API endpoint for sales analytics and revenue tracking data
// NOT for: Real analytics processing (will be replaced by backend API)

import { NextRequest, NextResponse } from 'next/server'

interface MockMarketplaceRevenue {
  marketplace: string
  revenue: number
  orders: number
  percentage: number
}

interface MockMonthlyRevenue {
  month: string
  revenue: number
  orders: number
}

interface MockTopProduct {
  id: string
  title: string
  marketplace: string
  revenue: number
  units_sold: number
  conversion_rate: number
}

// WHY: 5 marketplaces matching the rest of the app
const MARKETPLACE_REVENUE: MockMarketplaceRevenue[] = [
  { marketplace: 'Amazon', revenue: 48750, orders: 1245, percentage: 42.3 },
  { marketplace: 'eBay', revenue: 22340, orders: 687, percentage: 19.4 },
  { marketplace: 'Walmart', revenue: 18920, orders: 534, percentage: 16.4 },
  { marketplace: 'Shopify', revenue: 15680, orders: 412, percentage: 13.6 },
  { marketplace: 'Allegro', revenue: 9580, orders: 298, percentage: 8.3 },
]

// WHY: 6 months of data to show a meaningful trend
const MONTHLY_REVENUE: MockMonthlyRevenue[] = [
  { month: 'Sep 2025', revenue: 15200, orders: 398 },
  { month: 'Oct 2025', revenue: 18400, orders: 472 },
  { month: 'Nov 2025', revenue: 24600, orders: 621 },
  { month: 'Dec 2025', revenue: 28900, orders: 745 },
  { month: 'Jan 2026', revenue: 22100, orders: 587 },
  { month: 'Feb 2026', revenue: 6070, orders: 353 },
]

// WHY: 8 products sorted by revenue to fill a useful table
const TOP_PRODUCTS: MockTopProduct[] = [
  { id: 'tp-001', title: 'Premium Wireless Bluetooth Headphones with Active Noise Cancelling', marketplace: 'Amazon', revenue: 12450, units_sold: 415, conversion_rate: 8.2 },
  { id: 'tp-002', title: 'RGB Mechanical Gaming Keyboard Cherry MX Red Switches', marketplace: 'eBay', revenue: 9870, units_sold: 329, conversion_rate: 6.1 },
  { id: 'tp-003', title: 'Kids Learning Tablet 10 inch with Parental Controls', marketplace: 'Walmart', revenue: 8340, units_sold: 167, conversion_rate: 4.5 },
  { id: 'tp-004', title: 'Extra Thick Non-Slip Yoga Mat with Alignment Lines', marketplace: 'Shopify', revenue: 7200, units_sold: 480, conversion_rate: 7.8 },
  { id: 'tp-005', title: 'Noise Cancelling Over-Ear Headphones with 40h Battery', marketplace: 'Amazon', revenue: 6580, units_sold: 219, conversion_rate: 5.3 },
  { id: 'tp-006', title: 'Genuine Leather Bifold Wallet for Men RFID Blocking', marketplace: 'eBay', revenue: 5430, units_sold: 362, conversion_rate: 3.9 },
  { id: 'tp-007', title: 'Etui Samsung Galaxy S24 Ultra Pancerne z Klapką', marketplace: 'Allegro', revenue: 4120, units_sold: 515, conversion_rate: 1.8 },
  { id: 'tp-008', title: 'Ultrasonic Humidifier and Aromatherapy Diffuser 2-in-1', marketplace: 'Shopify', revenue: 3680, units_sold: 184, conversion_rate: 2.4 },
]

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const marketplace = searchParams.get('marketplace')
  const period = searchParams.get('period')

  let filteredMarketplace = [...MARKETPLACE_REVENUE]
  let filteredProducts = [...TOP_PRODUCTS]

  // WHY: When a marketplace is selected, only show that marketplace's data
  if (marketplace) {
    filteredMarketplace = filteredMarketplace.filter(
      (m) => m.marketplace === marketplace
    )
    filteredProducts = filteredProducts.filter(
      (p) => p.marketplace === marketplace
    )
    // Recalculate percentages when filtered to single marketplace
    if (filteredMarketplace.length === 1) {
      filteredMarketplace[0] = { ...filteredMarketplace[0], percentage: 100 }
    }
  }

  // WHY: Period affects monthly data window (mock: always return same data, but label it)
  // In production this would query different date ranges
  let filteredMonthly = [...MONTHLY_REVENUE]
  if (period === '7d') {
    filteredMonthly = filteredMonthly.slice(-1)
  } else if (period === '30d') {
    filteredMonthly = filteredMonthly.slice(-2)
  } else if (period === '90d') {
    filteredMonthly = filteredMonthly.slice(-3)
  }

  const totalRevenue = filteredMarketplace.reduce((sum, m) => sum + m.revenue, 0)
  const totalOrders = filteredMarketplace.reduce((sum, m) => sum + m.orders, 0)
  const avgOrderValue = totalOrders > 0 ? Math.round((totalRevenue / totalOrders) * 100) / 100 : 0
  // WHY: Conversion rate is a mock aggregate - in production would be calculated from sessions
  const conversionRate = 4.7

  return NextResponse.json({
    total_revenue: totalRevenue,
    total_orders: totalOrders,
    conversion_rate: conversionRate,
    avg_order_value: avgOrderValue,
    revenue_by_marketplace: filteredMarketplace,
    monthly_revenue: filteredMonthly,
    top_products: filteredProducts,
  })
}
