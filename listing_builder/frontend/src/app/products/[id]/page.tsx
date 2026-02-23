// frontend/src/app/products/[id]/page.tsx
// Purpose: Single product detail view with edit mode and optimization options
// NOT for: Product list or bulk operations

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useProduct, useUpdateProduct } from '@/lib/hooks/useProducts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { formatDate, getStatusColor, getStatusLabel, cn, getScoreColor, SAFE_HTML_TAGS } from '@/lib/utils'
import { ArrowLeft, Sparkles, Download, Pencil, Save, X, Plus, Trash2 } from 'lucide-react'
import DOMPurify from 'dompurify'
import ProductImageGallery from '@/components/ui/ProductImageGallery'
import type { Product } from '@/lib/types'

// WHY: Next.js 14 passes params as plain object, not Promise (that's Next.js 15+)
export default function ProductDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const { data: product, isLoading, error } = useProduct(params.id)
  const updateMutation = useUpdateProduct()

  // Edit mode state
  const [isEditing, setIsEditing] = useState(false)
  const [form, setForm] = useState<Partial<Product>>({})

  const startEditing = () => {
    if (!product) return
    setForm({
      title_original: product.title_original,
      title_optimized: product.title_optimized,
      description_original: product.description_original,
      description_optimized: product.description_optimized,
      brand: product.brand,
      category: product.category,
      price: product.price,
      attributes: { ...product.attributes },
    })
    setIsEditing(true)
  }

  const handleSave = () => {
    updateMutation.mutate(
      { id: params.id, data: form },
      { onSuccess: () => setIsEditing(false) },
    )
  }

  const bullets = (form.attributes?.bullet_points as string[]) || []
  const updateBullet = (idx: number, val: string) => {
    const next = [...bullets]
    next[idx] = val
    setForm({ ...form, attributes: { ...form.attributes, bullet_points: next } })
  }
  const addBullet = () => setForm({ ...form, attributes: { ...form.attributes, bullet_points: [...bullets, ''] } })
  const removeBullet = (idx: number) => {
    setForm({ ...form, attributes: { ...form.attributes, bullet_points: bullets.filter((_, i) => i !== idx) } })
  }

  // WHY: Export this specific product as CSV — no need to go to /publish page
  const handleExportCSV = () => {
    if (!product) return
    const bullets = (product.attributes?.bullet_points as string[]) || []
    const rows = [
      ['Field', 'Value'],
      ['Title', product.title_optimized || product.title_original],
      ['Brand', product.brand || ''],
      ['Category', product.category || ''],
      ['Price', product.price?.toString() || ''],
      ['Description', product.description_optimized || product.description_original || ''],
      ...bullets.map((b, i) => [`Bullet ${i + 1}`, b]),
      ['Backend Keywords', ((product.attributes?.seo_keywords as string[]) || []).join(', ')],
    ]
    const csv = rows.map(r => r.map(c => `"${(c || '').replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `product-${product.id}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  // WHY: Pass both title (prefill) and product_id so optimizer can save back to this product
  const handleOptimize = () => {
    const title = product?.title_optimized || product?.title_original || ''
    router.push(`/optimize?prefill=${encodeURIComponent(title)}&product_id=${product?.id}`)
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}><ArrowLeft className="h-4 w-4 mr-2" />Wstecz</Button>
        <Card className="animate-pulse"><CardContent className="p-8"><div className="h-64 bg-gray-700 rounded" /></CardContent></Card>
      </div>
    )
  }

  if (error || !product) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}><ArrowLeft className="h-4 w-4 mr-2" />Wstecz</Button>
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
          <ArrowLeft className="h-4 w-4 mr-2" />Wstecz do produktów
        </Button>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <Button variant="outline" onClick={() => setIsEditing(false)}><X className="h-4 w-4 mr-1" />Anuluj</Button>
              <Button onClick={handleSave} disabled={updateMutation.isPending}>
                <Save className="h-4 w-4 mr-1" />{updateMutation.isPending ? 'Zapisywanie...' : 'Zapisz'}
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={startEditing}><Pencil className="h-4 w-4 mr-1" />Edytuj</Button>
              <Button variant="outline" onClick={handleOptimize}><Sparkles className="h-4 w-4 mr-1" />Optymalizuj</Button>
              <Button onClick={handleExportCSV}><Download className="h-4 w-4 mr-1" />Eksportuj CSV</Button>
            </>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-2xl mb-2">{product.title_optimized || product.title_original}</CardTitle>
              <div className="flex items-center gap-4 text-sm text-gray-400">
                {product.source_id && <span>ID: {product.source_id}</span>}
                {product.brand && <span>Marka: {product.brand}</span>}
                {product.category && <span>Kategoria: {product.category}</span>}
              </div>
            </div>
            <Badge className={cn('text-sm', getStatusColor(product.status))}>{getStatusLabel(product.status)}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Product images gallery */}
          {product.images?.length > 0 && <ProductImageGallery images={product.images} />}

          {/* Optimization Score (read-only always) */}
          {product.optimization_score != null && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">Wynik optymalizacji</span>
                <span className={cn('text-2xl font-bold', getScoreColor(product.optimization_score))}>{Math.round(product.optimization_score)}%</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div className={cn('h-2 rounded-full transition-all', product.optimization_score >= 80 ? 'bg-green-500' : product.optimization_score >= 60 ? 'bg-yellow-500' : 'bg-red-500')} style={{ width: `${product.optimization_score}%` }} />
              </div>
            </div>
          )}

          {/* Titles */}
          {isEditing ? (
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm text-gray-400">Tytul oryginalny</label>
                <Input value={form.title_original ?? ''} onChange={(e) => setForm({ ...form, title_original: e.target.value })} />
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-400">Tytul zoptymalizowany</label>
                <Input value={form.title_optimized ?? ''} onChange={(e) => setForm({ ...form, title_optimized: e.target.value })} />
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div>
                  <label className="mb-1 block text-sm text-gray-400">Marka</label>
                  <Input value={form.brand ?? ''} onChange={(e) => setForm({ ...form, brand: e.target.value })} />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-400">Kategoria</label>
                  <Input value={form.category ?? ''} onChange={(e) => setForm({ ...form, category: e.target.value })} />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-gray-400">Cena</label>
                  <Input type="number" step="0.01" value={form.price ?? ''} onChange={(e) => setForm({ ...form, price: e.target.value ? parseFloat(e.target.value) : null })} />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-400">Opis oryginalny</label>
                <textarea value={form.description_original ?? ''} onChange={(e) => setForm({ ...form, description_original: e.target.value })} rows={3} className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white placeholder-gray-600 focus:border-gray-600 focus:outline-none" />
              </div>
              <div>
                <label className="mb-1 block text-sm text-gray-400">Opis zoptymalizowany</label>
                <textarea value={form.description_optimized ?? ''} onChange={(e) => setForm({ ...form, description_optimized: e.target.value })} rows={3} className="w-full rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white placeholder-gray-600 focus:border-gray-600 focus:outline-none" />
              </div>
              {/* Bullet points editor */}
              <div>
                <label className="mb-1 block text-sm text-gray-400">Kluczowe cechy</label>
                <div className="space-y-2">
                  {bullets.map((b, idx) => (
                    <div key={idx} className="flex gap-2">
                      <Input value={b} onChange={(e) => updateBullet(idx, e.target.value)} placeholder={`Bullet ${idx + 1}`} />
                      <button onClick={() => removeBullet(idx)} className="rounded-lg border border-gray-800 px-2 text-gray-500 hover:border-red-800 hover:text-red-400"><Trash2 className="h-4 w-4" /></button>
                    </div>
                  ))}
                </div>
                <button onClick={addBullet} className="mt-2 flex items-center gap-1 text-xs text-gray-500 hover:text-white"><Plus className="h-3 w-3" /> Dodaj bullet</button>
              </div>
            </div>
          ) : (
            <>
              {/* Description (read mode) — WHY: Optimizer returns HTML (<p>, <b>, <ul>), so render it */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Opis</h3>
                {(product.description_optimized || product.description_original || '').includes('<') ? (
                  <div
                    className="text-gray-300 [&_p]:mb-3 [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:mb-3 [&_li]:mb-1 [&_b]:font-semibold [&_b]:text-white"
                    // WHY: DOMPurify strips <script>, onerror, etc. — imported data could contain XSS
                    dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(product.description_optimized || product.description_original || '', { ALLOWED_TAGS: SAFE_HTML_TAGS }) }}
                  />
                ) : (
                  <p className="text-gray-300 whitespace-pre-wrap">{product.description_optimized || product.description_original || 'Brak opisu'}</p>
                )}
              </div>
              {/* Bullet Points */}
              {Array.isArray(product.attributes?.bullet_points) && (product.attributes.bullet_points as string[]).length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Kluczowe cechy</h3>
                  <ul className="space-y-2">
                    {(product.attributes.bullet_points as string[]).map((bullet, index) => (
                      <li key={index} className="flex items-start gap-2 text-gray-300"><span className="text-white mt-1">•</span><span>{bullet}</span></li>
                    ))}
                  </ul>
                </div>
              )}
              {/* SEO Keywords */}
              {Array.isArray(product.attributes?.seo_keywords) && (product.attributes.seo_keywords as string[]).length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Slowa kluczowe SEO</h3>
                  <div className="flex flex-wrap gap-2">
                    {(product.attributes.seo_keywords as string[]).map((kw, i) => (
                      <Badge key={i} variant="outline" className="text-xs">{kw}</Badge>
                    ))}
                  </div>
                </div>
              )}
              {/* Price */}
              {product.price && (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Cena</h3>
                  <p className="text-2xl font-bold text-green-500">${product.price.toFixed(2)}</p>
                </div>
              )}
            </>
          )}

          {/* Metadata (always visible) */}
          <div className="border-t border-gray-800 pt-4">
            <div className="grid gap-2 text-sm text-gray-400">
              <div className="flex justify-between"><span>Utworzono:</span><span>{formatDate(product.created_at)}</span></div>
              <div className="flex justify-between"><span>Zaktualizowano:</span><span>{product.updated_at ? formatDate(product.updated_at) : '—'}</span></div>
              <div className="flex justify-between"><span>ID produktu:</span><span className="font-mono text-xs">{product.id}</span></div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
