// frontend/src/app/compliance/components/NewsTab.tsx
// Purpose: Marketplace news aggregator — RSS feeds with images, grouped by marketplace
// NOT for: Alert management or compliance checks (those are separate tabs)

'use client'

import { useState, useEffect } from 'react'
import {
  Newspaper,
  ExternalLink,
  Loader2,
  RefreshCw,
  Globe,
  Clock,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NewsItem {
  title: string
  link: string
  source: string
  pubDate: string
  description: string
  category: string
  thumbnail: string
}

type NewsCategory = 'all' | 'amazon' | 'allegro' | 'ebay' | 'kaufland' | 'ecommerce' | 'compliance'

// WHY: RSS feeds from major marketplace news sources — parsed via rss2json.com
// Direct RSS preferred (og:image works). Google News only where no direct feed exists.
const RSS_FEEDS = [
  // Amazon — direct feeds (og:image works for all)
  { url: 'https://channelx.world/category/amazon/feed/', source: 'ChannelX Amazon', category: 'amazon' },
  { url: 'https://www.junglescout.com/blog/feed/', source: 'Jungle Scout', category: 'amazon' },
  // Allegro
  { url: 'https://blog.allegro.tech/feed.xml', source: 'Allegro Tech Blog', category: 'allegro' },
  { url: 'https://news.google.com/rss/search?q=Allegro+marketplace+sprzedawcy&hl=pl&gl=PL&ceid=PL:pl', source: 'Allegro News', category: 'allegro' },
  // eBay — direct feeds (og:image works)
  { url: 'https://www.ebayinc.com/stories/news/rss/', source: 'eBay Inc.', category: 'ebay' },
  { url: 'https://channelx.world/category/ebay/feed/', source: 'ChannelX eBay', category: 'ebay' },
  // Kaufland — no direct RSS, Google News only (gradient placeholder expected)
  { url: 'https://news.google.com/rss/search?q=Kaufland+Global+Marketplace+ecommerce&hl=en&gl=DE&ceid=DE:en', source: 'Kaufland News', category: 'kaufland' },
  // E-commerce general — 3 direct feeds with working og:image
  { url: 'https://ecommercenews.eu/feed/', source: 'Ecommerce News EU', category: 'ecommerce' },
  { url: 'https://tamebay.com/feed', source: 'Tamebay', category: 'ecommerce' },
  { url: 'https://www.practicalecommerce.com/feed', source: 'Practical Ecommerce', category: 'ecommerce' },
  { url: 'https://sellerengine.com/feed/', source: 'SellerEngine', category: 'ecommerce' },
  // Compliance — Google News only (no direct compliance RSS feeds exist)
  { url: 'https://news.google.com/rss/search?q=EU+GPSR+EPR+product+safety+ecommerce+compliance&hl=en&gl=DE&ceid=DE:en', source: 'EU Compliance', category: 'compliance' },
  { url: 'https://news.google.com/rss/search?q=Amazon+eBay+marketplace+compliance+regulation&hl=en&gl=US&ceid=US:en', source: 'Marketplace Compliance', category: 'compliance' },
]

// WHY: rss2json.com free API (10k req/day) avoids CORS issues with direct RSS
const RSS_API = 'https://api.rss2json.com/v1/api.json?rss_url='

const CATEGORIES: { key: NewsCategory; label: string; icon: string; color: string }[] = [
  { key: 'all', label: 'Wszystkie', icon: '🌐', color: 'bg-white/10 text-white' },
  { key: 'amazon', label: 'Amazon', icon: '📦', color: 'bg-orange-500/10 text-orange-400 border-orange-500/20' },
  { key: 'allegro', label: 'Allegro', icon: '🇵🇱', color: 'bg-orange-500/10 text-orange-300 border-orange-500/20' },
  { key: 'ebay', label: 'eBay', icon: '🏷️', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  { key: 'kaufland', label: 'Kaufland', icon: '🇩🇪', color: 'bg-red-500/10 text-red-300 border-red-500/20' },
  { key: 'ecommerce', label: 'E-commerce', icon: '🛒', color: 'bg-green-500/10 text-green-400 border-green-500/20' },
  { key: 'compliance', label: 'Compliance', icon: '📋', color: 'bg-red-500/10 text-red-400 border-red-500/20' },
]

const SECTION_COLORS: Record<string, string> = {
  amazon: 'text-orange-400',
  allegro: 'text-orange-300',
  ebay: 'text-blue-400',
  kaufland: 'text-red-300',
  ecommerce: 'text-green-400',
  compliance: 'text-red-400',
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffH = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
  if (diffH < 1) return 'Przed chwilą'
  if (diffH < 24) return `${diffH}h temu`
  const diffD = Math.floor(diffH / 24)
  if (diffD < 7) return `${diffD}d temu`
  return date.toLocaleDateString('pl-PL')
}

// WHY: Fetch og:image from article URL when RSS doesn't include a thumbnail
function useOgImage(url: string, skip: boolean) {
  const [image, setImage] = useState<string | null>(null)
  useEffect(() => {
    if (skip || !url) return
    fetch(`/api/og-image?url=${encodeURIComponent(url)}`)
      .then((r) => r.json())
      .then((d) => { if (d.image) setImage(d.image) })
      .catch(() => {})
  }, [url, skip])
  return image
}

// WHY: Reusable card — shows thumbnail, title, source badge, description
function NewsCard({ item, featured = false }: { item: NewsItem; featured?: boolean }) {
  const [imgError, setImgError] = useState(false)
  // WHY: Only fetch og:image when RSS thumbnail is missing
  const ogImage = useOgImage(item.link, !!item.thumbnail)
  const displayImage = (item.thumbnail && !imgError) ? item.thumbnail : ogImage

  return (
    <a
      href={item.link}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        'group flex flex-col overflow-hidden rounded-xl border border-gray-800 bg-[#1A1A1A] transition-all hover:border-gray-600 hover:bg-[#222]',
        featured ? 'md:flex-row' : ''
      )}
    >
      {/* WHY: Thumbnail from rss2json — fallback to placeholder on error */}
      <div className={cn(
        'relative shrink-0 overflow-hidden bg-[#151515]',
        featured ? 'h-48 md:h-auto md:w-72' : 'h-40'
      )}>
        {displayImage ? (
          <img
            src={displayImage}
            alt=""
            className="h-full w-full object-cover transition-transform group-hover:scale-105"
            onError={() => setImgError(true)}
            loading="lazy"
          />
        ) : (
          <div className={cn(
            'flex h-full items-center justify-center',
            item.category === 'amazon' ? 'bg-gradient-to-br from-orange-950 to-[#1A1A1A]' :
            item.category === 'ecommerce' ? 'bg-gradient-to-br from-green-950 to-[#1A1A1A]' :
            item.category === 'compliance' ? 'bg-gradient-to-br from-red-950 to-[#1A1A1A]' :
            item.category === 'ebay' ? 'bg-gradient-to-br from-blue-950 to-[#1A1A1A]' :
            'bg-gradient-to-br from-gray-800 to-[#1A1A1A]'
          )}>
            <span className="text-3xl opacity-40">
              {CATEGORIES.find(c => c.key === item.category)?.icon || '📰'}
            </span>
          </div>
        )}
        <span className={cn(
          'absolute left-2 top-2 rounded px-2 py-0.5 text-[10px] font-semibold backdrop-blur-sm',
          SECTION_COLORS[item.category] ?? 'text-gray-400',
          'bg-black/60'
        )}>
          {item.source}
        </span>
      </div>

      <div className="flex flex-1 flex-col justify-between p-4">
        <div>
          <p className={cn(
            'font-semibold text-white group-hover:text-gray-200 line-clamp-2',
            featured ? 'text-base' : 'text-sm'
          )}>
            {item.title}
          </p>
          {item.description && (
            <p className={cn(
              'mt-1.5 text-gray-500 line-clamp-2',
              featured ? 'text-sm' : 'text-xs'
            )}>
              {item.description}
            </p>
          )}
        </div>
        <div className="mt-3 flex items-center justify-between">
          {item.pubDate && (
            <span className="flex items-center gap-1 text-[11px] text-gray-600">
              <Clock className="h-3 w-3" />
              {formatDate(item.pubDate)}
            </span>
          )}
          <ExternalLink className="h-3.5 w-3.5 text-gray-700 group-hover:text-gray-400" />
        </div>
      </div>
    </a>
  )
}

// WHY: Section renders one marketplace group with header + grid of cards
function MarketplaceSection({ category, items }: { category: string; items: NewsItem[] }) {
  const cat = CATEGORIES.find((c) => c.key === category)
  if (!cat || items.length === 0) return null

  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        <span className="text-lg">{cat.icon}</span>
        <h3 className={cn('font-semibold', SECTION_COLORS[category] ?? 'text-white')}>
          {cat.label}
        </h3>
        <span className="text-xs text-gray-600">({items.length})</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item, i) => (
          <NewsCard key={`${item.link}-${i}`} item={item} />
        ))}
      </div>
    </div>
  )
}

export default function NewsTab() {
  const [news, setNews] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [category, setCategory] = useState<NewsCategory>('all')

  const fetchNews = async () => {
    setLoading(true)
    setError(null)
    try {
      const results: NewsItem[] = []

      // WHY: Stagger requests by 200ms to avoid rss2json.com rate limiting (free tier)
      const fetchFeed = async (feed: typeof RSS_FEEDS[number]): Promise<NewsItem[]> => {
        try {
          const res = await fetch(`${RSS_API}${encodeURIComponent(feed.url)}`)
          if (!res.ok) return []
          const data = await res.json()
          if (data.status !== 'ok' || !data.items) return []

          return data.items.slice(0, 6).map((item: Record<string, unknown>) => {
            const desc = (item.description as string) || ''
            const imgMatch = desc.match(/<img[^>]+src=["']([^"']+)["']/)
            const thumb = (item.thumbnail as string)
              || (item.enclosure as Record<string, string>)?.link
              || imgMatch?.[1]
              || ''
            return {
              title: (item.title as string) || 'Bez tytułu',
              link: (item.link as string) || '#',
              source: feed.source,
              pubDate: (item.pubDate as string) || '',
              description: desc.replace(/<[^>]*>/g, '').slice(0, 200),
              category: feed.category,
              thumbnail: thumb,
            }
          })
        } catch {
          return []
        }
      }

      // WHY: Batches of 3 with 300ms delay between batches — rss2json free tier throttles parallel requests
      const feedResults: NewsItem[][] = []
      const BATCH_SIZE = 3
      for (let i = 0; i < RSS_FEEDS.length; i += BATCH_SIZE) {
        const batch = RSS_FEEDS.slice(i, i + BATCH_SIZE)
        const batchResults = await Promise.all(batch.map(fetchFeed))
        feedResults.push(...batchResults)
        if (i + BATCH_SIZE < RSS_FEEDS.length) {
          await new Promise((r) => setTimeout(r, 300))
        }
      }
      for (const items of feedResults) results.push(...items)
      results.sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
      setNews(results)
    } catch {
      setError('Nie udało się załadować wiadomości')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchNews() }, [])

  const filteredNews = category === 'all' ? news : news.filter((n) => n.category === category)

  // WHY: Group by marketplace for "all" view — each section shows its own grid
  const groupedByMarketplace = ['amazon', 'allegro', 'ebay', 'kaufland', 'ecommerce', 'compliance']
    .map((cat) => ({ category: cat, items: news.filter((n) => n.category === cat) }))
    .filter((g) => g.items.length > 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Newspaper className="h-5 w-5 text-blue-400" />
            Wiadomości Marketplace
          </h2>
          <p className="text-sm text-gray-400">
            Najnowsze informacje z rynków e-commerce
          </p>
        </div>
        <button
          onClick={fetchNews}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg border border-gray-700 bg-[#1A1A1A] px-3 py-1.5 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
          Odśwież
        </button>
      </div>

      {/* Category filter pills */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {CATEGORIES.map((cat) => {
          const count = cat.key === 'all' ? news.length : news.filter((n) => n.category === cat.key).length
          return (
            <button
              key={cat.key}
              onClick={() => setCategory(cat.key)}
              className={cn(
                'flex items-center gap-1.5 whitespace-nowrap rounded-lg border px-3 py-1.5 text-sm transition-colors',
                category === cat.key
                  ? cn(cat.color, 'border-current/20')
                  : 'border-gray-800 text-gray-400 hover:text-white hover:border-gray-600'
              )}
            >
              <span>{cat.icon}</span>
              {cat.label}
              {count > 0 && <span className="text-xs opacity-60">({count})</span>}
            </button>
          )
        })}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
          <p className="text-sm text-gray-500">Pobieranie wiadomości...</p>
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-900 bg-red-950/30 p-6 text-center text-sm text-red-400">
          {error}
        </div>
      ) : filteredNews.length === 0 ? (
        <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-10 text-center">
          <Globe className="mx-auto h-10 w-10 text-gray-600 mb-3" />
          <p className="text-white font-medium">Brak wiadomości</p>
          <p className="text-sm text-gray-500 mt-1">
            {category === 'all'
              ? 'Nie znaleziono żadnych wiadomości'
              : `Brak wiadomości z kategorii "${CATEGORIES.find((c) => c.key === category)?.label}"`}
          </p>
        </div>
      ) : category === 'all' ? (
        /* WHY: "Wszystkie" view — hero card + sections per marketplace */
        <div className="space-y-8">
          {/* Hero: newest article with image */}
          {filteredNews[0] && (
            <NewsCard item={filteredNews[0]} featured />
          )}

          {/* Sections per marketplace */}
          {groupedByMarketplace.map((group) => (
            <MarketplaceSection key={group.category} category={group.category} items={group.items} />
          ))}
        </div>
      ) : (
        /* WHY: Single marketplace view — grid of cards */
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filteredNews.map((item, i) => (
            <NewsCard key={`${item.link}-${i}`} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}
