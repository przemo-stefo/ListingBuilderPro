// frontend/src/app/api/listings/route.ts
// Purpose: Mock API endpoint for compliance-focused listings data
// NOT for: Real marketplace integration (will be replaced by backend API)

import { NextRequest, NextResponse } from 'next/server'

interface MockListing {
  sku: string
  title: string
  marketplace: string
  compliance_status: 'compliant' | 'warning' | 'suppressed' | 'blocked'
  issues_count: number
  last_checked: string
}

// 10 hardcoded listings across all 5 marketplaces
const MOCK_LISTINGS: MockListing[] = [
  {
    sku: 'AMZ-001',
    title: 'Wireless Bluetooth Headphones - Noise Cancelling',
    marketplace: 'Amazon',
    compliance_status: 'compliant',
    issues_count: 0,
    last_checked: '2026-02-02T08:30:00Z',
  },
  {
    sku: 'AMZ-002',
    title: 'Organic Green Tea - 100 Bags',
    marketplace: 'Amazon',
    compliance_status: 'warning',
    issues_count: 2,
    last_checked: '2026-02-01T14:15:00Z',
  },
  {
    sku: 'EBY-001',
    title: 'Vintage Leather Wallet - Handmade',
    marketplace: 'eBay',
    compliance_status: 'compliant',
    issues_count: 0,
    last_checked: '2026-02-02T09:00:00Z',
  },
  {
    sku: 'EBY-002',
    title: 'Mechanical Gaming Keyboard RGB',
    marketplace: 'eBay',
    compliance_status: 'suppressed',
    issues_count: 3,
    last_checked: '2026-01-31T18:45:00Z',
  },
  {
    sku: 'WMT-001',
    title: 'Stainless Steel Water Bottle 32oz',
    marketplace: 'Walmart',
    compliance_status: 'compliant',
    issues_count: 0,
    last_checked: '2026-02-02T07:00:00Z',
  },
  {
    sku: 'WMT-002',
    title: 'Kids Educational Tablet - Learning Toy',
    marketplace: 'Walmart',
    compliance_status: 'blocked',
    issues_count: 5,
    last_checked: '2026-01-30T12:00:00Z',
  },
  {
    sku: 'SHP-001',
    title: 'Yoga Mat Non-Slip Premium',
    marketplace: 'Shopify',
    compliance_status: 'compliant',
    issues_count: 0,
    last_checked: '2026-02-02T10:30:00Z',
  },
  {
    sku: 'SHP-002',
    title: 'Essential Oil Diffuser - Aromatherapy',
    marketplace: 'Shopify',
    compliance_status: 'warning',
    issues_count: 1,
    last_checked: '2026-02-01T16:20:00Z',
  },
  {
    sku: 'ALG-001',
    title: 'Etui na telefon Samsung Galaxy S24',
    marketplace: 'Allegro',
    compliance_status: 'warning',
    issues_count: 1,
    last_checked: '2026-02-01T20:00:00Z',
  },
  {
    sku: 'ALG-002',
    title: 'Kabel USB-C Lightning 2m MFi',
    marketplace: 'Allegro',
    compliance_status: 'suppressed',
    issues_count: 4,
    last_checked: '2026-01-29T11:30:00Z',
  },
]

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const marketplace = searchParams.get('marketplace')
  const complianceStatus = searchParams.get('compliance_status')

  // Filter listings based on query params
  let filtered = [...MOCK_LISTINGS]

  if (marketplace) {
    filtered = filtered.filter((l) => l.marketplace === marketplace)
  }

  if (complianceStatus) {
    filtered = filtered.filter((l) => l.compliance_status === complianceStatus)
  }

  // Compute counts from full dataset (before filtering, so cards stay consistent)
  const compliant_count = MOCK_LISTINGS.filter((l) => l.compliance_status === 'compliant').length
  const warning_count = MOCK_LISTINGS.filter((l) => l.compliance_status === 'warning').length
  const suppressed_count = MOCK_LISTINGS.filter((l) => l.compliance_status === 'suppressed').length
  const blocked_count = MOCK_LISTINGS.filter((l) => l.compliance_status === 'blocked').length

  return NextResponse.json({
    listings: filtered,
    total: MOCK_LISTINGS.length,
    compliant_count,
    warning_count,
    suppressed_count,
    blocked_count,
  })
}
