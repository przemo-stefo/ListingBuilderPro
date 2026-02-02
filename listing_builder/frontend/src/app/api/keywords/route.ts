// frontend/src/app/api/keywords/route.ts
// Purpose: Mock API endpoint for keyword tracking data
// NOT for: Real SEO integration (will be replaced by backend API)

import { NextRequest, NextResponse } from 'next/server'

interface MockKeyword {
  id: string
  keyword: string
  search_volume: number
  current_rank: number | null
  marketplace: string
  trend: 'up' | 'down' | 'stable'
  relevance_score: number
  last_updated: string
}

// 15 hardcoded keywords, 3 per marketplace
const MOCK_KEYWORDS: MockKeyword[] = [
  {
    id: 'kw-001',
    keyword: 'wireless bluetooth headphones',
    search_volume: 245000,
    current_rank: 3,
    marketplace: 'Amazon',
    trend: 'up',
    relevance_score: 95,
    last_updated: '2026-02-02T08:30:00Z',
  },
  {
    id: 'kw-002',
    keyword: 'noise cancelling earbuds',
    search_volume: 182000,
    current_rank: 12,
    marketplace: 'Amazon',
    trend: 'stable',
    relevance_score: 88,
    last_updated: '2026-02-02T08:30:00Z',
  },
  {
    id: 'kw-003',
    keyword: 'organic green tea bags',
    search_volume: 74000,
    current_rank: 7,
    marketplace: 'Amazon',
    trend: 'down',
    relevance_score: 72,
    last_updated: '2026-02-01T14:15:00Z',
  },
  {
    id: 'kw-004',
    keyword: 'vintage leather wallet men',
    search_volume: 31000,
    current_rank: 22,
    marketplace: 'eBay',
    trend: 'up',
    relevance_score: 81,
    last_updated: '2026-02-02T09:00:00Z',
  },
  {
    id: 'kw-005',
    keyword: 'mechanical gaming keyboard',
    search_volume: 198000,
    current_rank: 5,
    marketplace: 'eBay',
    trend: 'up',
    relevance_score: 93,
    last_updated: '2026-02-02T09:00:00Z',
  },
  {
    id: 'kw-006',
    keyword: 'rgb keyboard cherry mx',
    search_volume: 45000,
    current_rank: 67,
    marketplace: 'eBay',
    trend: 'down',
    relevance_score: 54,
    last_updated: '2026-01-31T18:45:00Z',
  },
  {
    id: 'kw-007',
    keyword: 'stainless steel water bottle',
    search_volume: 156000,
    current_rank: 9,
    marketplace: 'Walmart',
    trend: 'stable',
    relevance_score: 90,
    last_updated: '2026-02-02T07:00:00Z',
  },
  {
    id: 'kw-008',
    keyword: 'kids learning tablet',
    search_volume: 89000,
    current_rank: 34,
    marketplace: 'Walmart',
    trend: 'down',
    relevance_score: 65,
    last_updated: '2026-01-30T12:00:00Z',
  },
  {
    id: 'kw-009',
    keyword: 'insulated water bottle 32oz',
    search_volume: 67000,
    current_rank: null,
    marketplace: 'Walmart',
    trend: 'stable',
    relevance_score: 78,
    last_updated: '2026-02-01T10:00:00Z',
  },
  {
    id: 'kw-010',
    keyword: 'non slip yoga mat',
    search_volume: 112000,
    current_rank: 2,
    marketplace: 'Shopify',
    trend: 'up',
    relevance_score: 97,
    last_updated: '2026-02-02T10:30:00Z',
  },
  {
    id: 'kw-011',
    keyword: 'essential oil diffuser',
    search_volume: 134000,
    current_rank: 15,
    marketplace: 'Shopify',
    trend: 'stable',
    relevance_score: 82,
    last_updated: '2026-02-01T16:20:00Z',
  },
  {
    id: 'kw-012',
    keyword: 'aromatherapy diffuser led',
    search_volume: 28000,
    current_rank: 41,
    marketplace: 'Shopify',
    trend: 'down',
    relevance_score: 59,
    last_updated: '2026-02-01T16:20:00Z',
  },
  {
    id: 'kw-013',
    keyword: 'etui samsung galaxy s24',
    search_volume: 52000,
    current_rank: 8,
    marketplace: 'Allegro',
    trend: 'up',
    relevance_score: 91,
    last_updated: '2026-02-01T20:00:00Z',
  },
  {
    id: 'kw-014',
    keyword: 'kabel usb-c lightning mfi',
    search_volume: 38000,
    current_rank: 19,
    marketplace: 'Allegro',
    trend: 'stable',
    relevance_score: 76,
    last_updated: '2026-02-01T20:00:00Z',
  },
  {
    id: 'kw-015',
    keyword: 'ładowarka indukcyjna qi',
    search_volume: 61000,
    current_rank: null,
    marketplace: 'Allegro',
    trend: 'up',
    relevance_score: 84,
    last_updated: '2026-01-29T11:30:00Z',
  },
]

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const marketplace = searchParams.get('marketplace')
  const search = searchParams.get('search')

  // Filter keywords based on query params
  let filtered = [...MOCK_KEYWORDS]

  if (marketplace) {
    filtered = filtered.filter((k) => k.marketplace === marketplace)
  }

  if (search) {
    const lower = search.toLowerCase()
    filtered = filtered.filter((k) => k.keyword.toLowerCase().includes(lower))
  }

  // Summary counts from full dataset (unfiltered) so cards stay consistent
  const tracked_count = MOCK_KEYWORDS.filter((k) => k.current_rank !== null).length
  const top_10_count = MOCK_KEYWORDS.filter(
    (k) => k.current_rank !== null && k.current_rank <= 10
  ).length
  const avg_relevance = Math.round(
    MOCK_KEYWORDS.reduce((sum, k) => sum + k.relevance_score, 0) / MOCK_KEYWORDS.length
  )

  return NextResponse.json({
    keywords: filtered,
    total: MOCK_KEYWORDS.length,
    tracked_count,
    top_10_count,
    avg_relevance,
  })
}
