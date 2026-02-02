// frontend/src/app/api/inventory/route.ts
// Purpose: Mock API endpoint for inventory/stock level tracking data
// NOT for: Real inventory management (will be replaced by backend API)

import { NextRequest, NextResponse } from 'next/server'

interface MockInventoryItem {
  id: string
  sku: string
  product_title: string
  marketplace: string
  quantity: number
  reorder_point: number
  days_of_supply: number
  status: 'in_stock' | 'low_stock' | 'out_of_stock' | 'overstock'
  unit_cost: number
  total_value: number
  last_restocked: string
}

// 15 hardcoded inventory items, 3 per marketplace
// WHY: 7 in_stock, 4 low_stock, 3 out_of_stock, 1 overstock to show all status variants
const MOCK_INVENTORY: MockInventoryItem[] = [
  {
    id: 'inv-001',
    sku: 'AMZ-WH-1001',
    product_title: 'Premium Wireless Bluetooth Headphones with Active Noise Cancelling',
    marketplace: 'Amazon',
    quantity: 342,
    reorder_point: 100,
    days_of_supply: 45,
    status: 'in_stock',
    unit_cost: 18.50,
    total_value: 6327.00,
    last_restocked: '2026-01-28T10:00:00Z',
  },
  {
    id: 'inv-002',
    sku: 'AMZ-WH-1002',
    product_title: 'Noise Cancelling Over-Ear Headphones with 40h Battery',
    marketplace: 'Amazon',
    quantity: 45,
    reorder_point: 80,
    days_of_supply: 12,
    status: 'low_stock',
    unit_cost: 22.00,
    total_value: 990.00,
    last_restocked: '2026-01-15T08:30:00Z',
  },
  {
    id: 'inv-003',
    sku: 'AMZ-WH-1003',
    product_title: 'Deep Bass Wireless Headphones Foldable Design',
    marketplace: 'Amazon',
    quantity: 0,
    reorder_point: 60,
    days_of_supply: 0,
    status: 'out_of_stock',
    unit_cost: 14.75,
    total_value: 0,
    last_restocked: '2025-12-20T14:00:00Z',
  },
  {
    id: 'inv-004',
    sku: 'EBY-LW-2001',
    product_title: 'Genuine Leather Bifold Wallet for Men RFID Blocking',
    marketplace: 'eBay',
    quantity: 187,
    reorder_point: 50,
    days_of_supply: 62,
    status: 'in_stock',
    unit_cost: 8.25,
    total_value: 1542.75,
    last_restocked: '2026-01-25T09:00:00Z',
  },
  {
    id: 'inv-005',
    sku: 'EBY-KB-2002',
    product_title: 'RGB Mechanical Gaming Keyboard Cherry MX Red Switches',
    marketplace: 'eBay',
    quantity: 23,
    reorder_point: 40,
    days_of_supply: 8,
    status: 'low_stock',
    unit_cost: 35.00,
    total_value: 805.00,
    last_restocked: '2026-01-10T12:00:00Z',
  },
  {
    id: 'inv-006',
    sku: 'EBY-MS-2003',
    product_title: 'Wireless Gaming Mouse 16000 DPI Ergonomic Design',
    marketplace: 'eBay',
    quantity: 256,
    reorder_point: 60,
    days_of_supply: 55,
    status: 'in_stock',
    unit_cost: 12.00,
    total_value: 3072.00,
    last_restocked: '2026-01-30T16:00:00Z',
  },
  {
    id: 'inv-007',
    sku: 'WMT-WB-3001',
    product_title: 'Insulated Stainless Steel Water Bottle 32oz Wide Mouth',
    marketplace: 'Walmart',
    quantity: 0,
    reorder_point: 100,
    days_of_supply: 0,
    status: 'out_of_stock',
    unit_cost: 6.50,
    total_value: 0,
    last_restocked: '2025-12-15T07:00:00Z',
  },
  {
    id: 'inv-008',
    sku: 'WMT-TB-3002',
    product_title: 'Kids Learning Tablet 10 inch with Parental Controls',
    marketplace: 'Walmart',
    quantity: 128,
    reorder_point: 30,
    days_of_supply: 38,
    status: 'in_stock',
    unit_cost: 45.00,
    total_value: 5760.00,
    last_restocked: '2026-01-20T11:00:00Z',
  },
  {
    id: 'inv-009',
    sku: 'WMT-WB-3003',
    product_title: 'Vacuum Insulated Sports Bottle with Straw Lid',
    marketplace: 'Walmart',
    quantity: 890,
    reorder_point: 100,
    days_of_supply: 120,
    status: 'overstock',
    unit_cost: 5.25,
    total_value: 4672.50,
    last_restocked: '2026-01-05T08:00:00Z',
  },
  {
    id: 'inv-010',
    sku: 'SHP-YM-4001',
    product_title: 'Extra Thick Non-Slip Yoga Mat with Alignment Lines',
    marketplace: 'Shopify',
    quantity: 215,
    reorder_point: 50,
    days_of_supply: 72,
    status: 'in_stock',
    unit_cost: 9.00,
    total_value: 1935.00,
    last_restocked: '2026-01-22T10:30:00Z',
  },
  {
    id: 'inv-011',
    sku: 'SHP-DF-4002',
    product_title: 'Essential Oil Diffuser 500ml LED Color Changing',
    marketplace: 'Shopify',
    quantity: 18,
    reorder_point: 35,
    days_of_supply: 6,
    status: 'low_stock',
    unit_cost: 11.50,
    total_value: 207.00,
    last_restocked: '2026-01-08T16:20:00Z',
  },
  {
    id: 'inv-012',
    sku: 'SHP-DF-4003',
    product_title: 'Ultrasonic Humidifier and Aromatherapy Diffuser 2-in-1',
    marketplace: 'Shopify',
    quantity: 154,
    reorder_point: 40,
    days_of_supply: 42,
    status: 'in_stock',
    unit_cost: 13.00,
    total_value: 2002.00,
    last_restocked: '2026-01-18T14:00:00Z',
  },
  {
    id: 'inv-013',
    sku: 'ALG-PC-5001',
    product_title: 'Etui Samsung Galaxy S24 Ultra Pancerne z Klapką',
    marketplace: 'Allegro',
    quantity: 312,
    reorder_point: 80,
    days_of_supply: 52,
    status: 'in_stock',
    unit_cost: 4.50,
    total_value: 1404.00,
    last_restocked: '2026-01-26T20:00:00Z',
  },
  {
    id: 'inv-014',
    sku: 'ALG-CB-5002',
    product_title: 'Kabel USB-C Lightning MFi 2m Szybkie Ładowanie',
    marketplace: 'Allegro',
    quantity: 0,
    reorder_point: 100,
    days_of_supply: 0,
    status: 'out_of_stock',
    unit_cost: 3.25,
    total_value: 0,
    last_restocked: '2025-12-28T20:00:00Z',
  },
  {
    id: 'inv-015',
    sku: 'ALG-CH-5003',
    product_title: 'Ładowarka Indukcyjna Qi 15W Kompatybilna z iPhone Samsung',
    marketplace: 'Allegro',
    quantity: 67,
    reorder_point: 70,
    days_of_supply: 22,
    status: 'low_stock',
    unit_cost: 7.80,
    total_value: 522.60,
    last_restocked: '2026-01-12T11:30:00Z',
  },
]

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const marketplace = searchParams.get('marketplace')
  const status = searchParams.get('status')
  const search = searchParams.get('search')

  // Filter inventory based on query params
  let filtered = [...MOCK_INVENTORY]

  if (marketplace) {
    filtered = filtered.filter((item) => item.marketplace === marketplace)
  }

  if (status) {
    filtered = filtered.filter((item) => item.status === status)
  }

  if (search) {
    const lower = search.toLowerCase()
    // WHY: Search both SKU and product title for flexibility
    filtered = filtered.filter(
      (item) =>
        item.sku.toLowerCase().includes(lower) ||
        item.product_title.toLowerCase().includes(lower)
    )
  }

  // Summary counts from full dataset (unfiltered) so cards stay consistent
  const in_stock_count = MOCK_INVENTORY.filter((i) => i.status === 'in_stock').length
  const low_stock_count = MOCK_INVENTORY.filter((i) => i.status === 'low_stock').length
  const out_of_stock_count = MOCK_INVENTORY.filter((i) => i.status === 'out_of_stock').length
  const total_value = Math.round(
    MOCK_INVENTORY.reduce((sum, i) => sum + i.total_value, 0) * 100
  ) / 100

  return NextResponse.json({
    items: filtered,
    total: MOCK_INVENTORY.length,
    in_stock_count,
    low_stock_count,
    out_of_stock_count,
    total_value,
  })
}
