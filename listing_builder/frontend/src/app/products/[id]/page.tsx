// frontend/src/app/products/[id]/page.tsx
// Purpose: Single product detail view with optimization options
// NOT for: Product list or bulk operations

'use client'

import { useRouter } from 'next/navigation'
import { useProduct } from '@/lib/hooks/useProducts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { formatDate, getStatusColor, cn, getScoreColor } from '@/lib/utils'
import { ArrowLeft, Sparkles, Send } from 'lucide-react'

// WHY: Next.js 14 passes params as plain object, not Promise (that's Next.js 15+)
export default function ProductDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const { data: product, isLoading, error } = useProduct(params.id)

  // WHY: Navigate to optimizer with product title pre-filled instead of
  // calling a broken /ai/optimize endpoint that doesn't exist on backend.
  const handleOptimize = () => {
    const title = product?.title_optimized || product?.title_original || ''
    router.push(`/optimize?product=${encodeURIComponent(title)}`)
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Wstecz
        </Button>
        <Card className="animate-pulse">
          <CardContent className="p-8">
            <div className="h-64 bg-gray-700 rounded" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error || !product) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Wstecz
        </Button>
        <Card className="border-red-500">
          <CardHeader>
            <CardTitle className="text-red-500">Produkt nie znaleziony</CardTitle>
            <CardDescription>Produkt, którego szukasz, nie istnieje</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Wstecz do produktów
        </Button>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleOptimize}
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Optymalizuj
          </Button>
          <Button onClick={() => router.push('/publish')}>
            <Send className="h-4 w-4 mr-2" />
            Eksportuj
          </Button>
        </div>
      </div>

      {/* Product Info */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-2xl mb-2">
                {product.title_optimized || product.title_original}
              </CardTitle>
              <div className="flex items-center gap-4 text-sm text-gray-400">
                {product.source_id && <span>ID: {product.source_id}</span>}
                {product.brand && <span>Marka: {product.brand}</span>}
                {product.category && <span>Kategoria: {product.category}</span>}
                {product.source_platform && <span>Platforma: {product.source_platform}</span>}
              </div>
            </div>
            <Badge className={cn('text-sm', getStatusColor(product.status))}>
              {product.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Optimization Score */}
          {product.optimization_score != null && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">Wynik optymalizacji</span>
                <span className={cn('text-2xl font-bold', getScoreColor(product.optimization_score))}>
                  {Math.round(product.optimization_score)}%
                </span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div
                  className={cn(
                    'h-2 rounded-full transition-all',
                    product.optimization_score >= 80 ? 'bg-green-500' :
                    product.optimization_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                  )}
                  style={{ width: `${product.optimization_score}%` }}
                />
              </div>
            </div>
          )}

          {/* Description */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Opis</h3>
            <p className="text-gray-300 whitespace-pre-wrap">
              {product.description_optimized || product.description_original || 'Brak opisu'}
            </p>
          </div>

          {/* Bullet Points — stored in attributes if present */}
          {Array.isArray(product.attributes?.bullet_points) && (product.attributes.bullet_points as string[]).length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Kluczowe cechy</h3>
              <ul className="space-y-2">
                {(product.attributes.bullet_points as string[]).map((bullet, index) => (
                  <li key={index} className="flex items-start gap-2 text-gray-300">
                    <span className="text-white mt-1">•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* SEO Keywords — stored in attributes if present */}
          {Array.isArray(product.attributes?.seo_keywords) && (product.attributes.seo_keywords as string[]).length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Słowa kluczowe SEO</h3>
              <div className="flex flex-wrap gap-2">
                {(product.attributes.seo_keywords as string[]).map((keyword, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {keyword}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Price */}
          {product.price && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Cena</h3>
              <p className="text-2xl font-bold text-green-500">
                ${product.price.toFixed(2)}
              </p>
            </div>
          )}

          {/* Metadata */}
          <div className="border-t border-gray-800 pt-4">
            <div className="grid gap-2 text-sm text-gray-400">
              <div className="flex justify-between">
                <span>Utworzono:</span>
                <span>{formatDate(product.created_at)}</span>
              </div>
              <div className="flex justify-between">
                <span>Zaktualizowano:</span>
                <span>{product.updated_at ? formatDate(product.updated_at) : '—'}</span>
              </div>
              <div className="flex justify-between">
                <span>ID produktu:</span>
                <span className="font-mono text-xs">{product.id}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
