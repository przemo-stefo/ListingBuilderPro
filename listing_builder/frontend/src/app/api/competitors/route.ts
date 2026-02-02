// frontend/src/app/api/competitors/route.ts
// Purpose: Mock API endpoint for competitor tracking data
// NOT for: Real competitor intelligence (will be replaced by backend API)

import { NextRequest, NextResponse } from 'next/server'

interface MockCompetitor {
  id: string
  competitor_name: string
  asin: string
  product_title: string
  marketplace: string
  their_price: number
  our_price: number
  price_difference: number
  their_rating: number
  their_reviews_count: number
  status: 'winning' | 'losing' | 'tied'
  last_checked: string
}

// 15 hardcoded competitors, 3 per marketplace
// WHY: 7 winning, 5 losing, 3 tied to show all status variants
const MOCK_COMPETITORS: MockCompetitor[] = [
  {
    id: 'comp-001',
    competitor_name: 'AudioTech Pro',
    asin: 'B09XYZABC1',
    product_title: 'Premium Wireless Bluetooth Headphones with Active Noise Cancelling',
    marketplace: 'Amazon',
    their_price: 79.99,
    our_price: 69.99,
    price_difference: 10.0,
    their_rating: 4.3,
    their_reviews_count: 2847,
    status: 'winning',
    last_checked: '2026-02-02T08:30:00Z',
  },
  {
    id: 'comp-002',
    competitor_name: 'SoundWave Elite',
    asin: 'B09XYZABC2',
    product_title: 'Noise Cancelling Over-Ear Headphones with 40h Battery',
    marketplace: 'Amazon',
    their_price: 54.99,
    our_price: 69.99,
    price_difference: -15.0,
    their_rating: 4.6,
    their_reviews_count: 5213,
    status: 'losing',
    last_checked: '2026-02-02T08:30:00Z',
  },
  {
    id: 'comp-003',
    competitor_name: 'BassKing Audio',
    asin: 'B09XYZABC3',
    product_title: 'Deep Bass Wireless Headphones Foldable Design',
    marketplace: 'Amazon',
    their_price: 69.99,
    our_price: 69.99,
    price_difference: 0,
    their_rating: 4.1,
    their_reviews_count: 1562,
    status: 'tied',
    last_checked: '2026-02-01T14:15:00Z',
  },
  {
    id: 'comp-004',
    competitor_name: 'LeatherCraft Co',
    asin: 'B09XYZDEF1',
    product_title: 'Genuine Leather Bifold Wallet for Men RFID Blocking',
    marketplace: 'eBay',
    their_price: 42.99,
    our_price: 34.99,
    price_difference: 8.0,
    their_rating: 4.5,
    their_reviews_count: 892,
    status: 'winning',
    last_checked: '2026-02-02T09:00:00Z',
  },
  {
    id: 'comp-005',
    competitor_name: 'KeyMaster Gaming',
    asin: 'B09XYZDEF2',
    product_title: 'RGB Mechanical Gaming Keyboard Cherry MX Red Switches',
    marketplace: 'eBay',
    their_price: 89.99,
    our_price: 99.99,
    price_difference: -10.0,
    their_rating: 4.7,
    their_reviews_count: 3421,
    status: 'losing',
    last_checked: '2026-02-02T09:00:00Z',
  },
  {
    id: 'comp-006',
    competitor_name: 'PeripheralPro',
    asin: 'B09XYZDEF3',
    product_title: 'Wireless Gaming Mouse 16000 DPI Ergonomic Design',
    marketplace: 'eBay',
    their_price: 45.99,
    our_price: 39.99,
    price_difference: 6.0,
    their_rating: 4.2,
    their_reviews_count: 1105,
    status: 'winning',
    last_checked: '2026-01-31T18:45:00Z',
  },
  {
    id: 'comp-007',
    competitor_name: 'HydroFlask Direct',
    asin: 'B09XYZGHI1',
    product_title: 'Insulated Stainless Steel Water Bottle 32oz Wide Mouth',
    marketplace: 'Walmart',
    their_price: 34.99,
    our_price: 29.99,
    price_difference: 5.0,
    their_rating: 4.8,
    their_reviews_count: 8934,
    status: 'winning',
    last_checked: '2026-02-02T07:00:00Z',
  },
  {
    id: 'comp-008',
    competitor_name: 'EduTab Kids',
    asin: 'B09XYZGHI2',
    product_title: 'Kids Learning Tablet 10 inch with Parental Controls',
    marketplace: 'Walmart',
    their_price: 119.99,
    our_price: 139.99,
    price_difference: -20.0,
    their_rating: 4.4,
    their_reviews_count: 2156,
    status: 'losing',
    last_checked: '2026-01-30T12:00:00Z',
  },
  {
    id: 'comp-009',
    competitor_name: 'CoolDrink Supply',
    asin: 'B09XYZGHI3',
    product_title: 'Vacuum Insulated Sports Bottle with Straw Lid',
    marketplace: 'Walmart',
    their_price: 29.99,
    our_price: 29.99,
    price_difference: 0,
    their_rating: 4.0,
    their_reviews_count: 743,
    status: 'tied',
    last_checked: '2026-02-01T10:00:00Z',
  },
  {
    id: 'comp-010',
    competitor_name: 'ZenYoga Gear',
    asin: 'B09XYZJKL1',
    product_title: 'Extra Thick Non-Slip Yoga Mat with Alignment Lines',
    marketplace: 'Shopify',
    their_price: 39.99,
    our_price: 32.99,
    price_difference: 7.0,
    their_rating: 4.6,
    their_reviews_count: 4521,
    status: 'winning',
    last_checked: '2026-02-02T10:30:00Z',
  },
  {
    id: 'comp-011',
    competitor_name: 'AromaLife Home',
    asin: 'B09XYZJKL2',
    product_title: 'Essential Oil Diffuser 500ml LED Color Changing',
    marketplace: 'Shopify',
    their_price: 24.99,
    our_price: 29.99,
    price_difference: -5.0,
    their_rating: 4.3,
    their_reviews_count: 1876,
    status: 'losing',
    last_checked: '2026-02-01T16:20:00Z',
  },
  {
    id: 'comp-012',
    competitor_name: 'MistMakers',
    asin: 'B09XYZJKL3',
    product_title: 'Ultrasonic Humidifier and Aromatherapy Diffuser 2-in-1',
    marketplace: 'Shopify',
    their_price: 29.99,
    our_price: 29.99,
    price_difference: 0,
    their_rating: 3.9,
    their_reviews_count: 654,
    status: 'tied',
    last_checked: '2026-02-01T16:20:00Z',
  },
  {
    id: 'comp-013',
    competitor_name: 'PhoneArmor PL',
    asin: 'ALG-98765A',
    product_title: 'Etui Samsung Galaxy S24 Ultra Pancerne z Klapką',
    marketplace: 'Allegro',
    their_price: 89.99,
    our_price: 79.99,
    price_difference: 10.0,
    their_rating: 4.4,
    their_reviews_count: 1243,
    status: 'winning',
    last_checked: '2026-02-01T20:00:00Z',
  },
  {
    id: 'comp-014',
    competitor_name: 'CableWorld PL',
    asin: 'ALG-98765B',
    product_title: 'Kabel USB-C Lightning MFi 2m Szybkie Ładowanie',
    marketplace: 'Allegro',
    their_price: 29.99,
    our_price: 39.99,
    price_difference: -10.0,
    their_rating: 4.5,
    their_reviews_count: 967,
    status: 'losing',
    last_checked: '2026-02-01T20:00:00Z',
  },
  {
    id: 'comp-015',
    competitor_name: 'TechCharge PL',
    asin: 'ALG-98765C',
    product_title: 'Ładowarka Indukcyjna Qi 15W Kompatybilna z iPhone Samsung',
    marketplace: 'Allegro',
    their_price: 59.99,
    our_price: 49.99,
    price_difference: 10.0,
    their_rating: 4.2,
    their_reviews_count: 534,
    status: 'winning',
    last_checked: '2026-01-29T11:30:00Z',
  },
]

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const marketplace = searchParams.get('marketplace')
  const search = searchParams.get('search')

  // Filter competitors based on query params
  let filtered = [...MOCK_COMPETITORS]

  if (marketplace) {
    filtered = filtered.filter((c) => c.marketplace === marketplace)
  }

  if (search) {
    const lower = search.toLowerCase()
    // WHY: Search both competitor name and product title for flexibility
    filtered = filtered.filter(
      (c) =>
        c.competitor_name.toLowerCase().includes(lower) ||
        c.product_title.toLowerCase().includes(lower)
    )
  }

  // Summary counts from full dataset (unfiltered) so cards stay consistent
  const winning_count = MOCK_COMPETITORS.filter((c) => c.status === 'winning').length
  const losing_count = MOCK_COMPETITORS.filter((c) => c.status === 'losing').length
  const avg_price_gap = Math.round(
    (MOCK_COMPETITORS.reduce((sum, c) => sum + Math.abs(c.price_difference), 0) /
      MOCK_COMPETITORS.length) *
      100
  ) / 100

  return NextResponse.json({
    competitors: filtered,
    total: MOCK_COMPETITORS.length,
    winning_count,
    losing_count,
    avg_price_gap,
  })
}
