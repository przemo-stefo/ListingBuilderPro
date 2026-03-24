// frontend/src/app/attributes/components/AttributeForm.tsx
// Purpose: 2-step form — product input → category selector → generate
// NOT for: Result display (AttributeResult.tsx) or history (AttributeHistory.tsx)

'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Search, Loader2, Link } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { searchCategories, resolveAllegroUrl } from '@/lib/api/attributes'
import { CategoryList } from './CategoryList'
import type { AllegroCategory } from '@/lib/types'

type Marketplace = 'allegro' | 'kaufland'

interface AttributeFormProps {
  onSubmit: (productInput: string, categoryId: string, categoryName: string, categoryPath: string, marketplace: Marketplace) => void
  isLoading: boolean
}

export function AttributeForm({ onSubmit, isLoading }: AttributeFormProps) {
  const [productInput, setProductInput] = useState('')
  const [marketplace, setMarketplace] = useState<Marketplace>('allegro')
  const [categories, setCategories] = useState<AllegroCategory[]>([])
  const [selectedCategory, setSelectedCategory] = useState<AllegroCategory | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [searched, setSearched] = useState(false)
  const [isResolving, setIsResolving] = useState(false)
  const [resolveError, setResolveError] = useState('')
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const doSearch = useCallback(async (query: string) => {
    // WHY: Cancel any in-flight request before starting a new one
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()

    setIsSearching(true)
    setSelectedCategory(null)
    setSearched(false)
    try {
      const data = await searchCategories(query, abortRef.current?.signal)
      setCategories(data.categories || [])
      setSearched(true)
    } catch (e: unknown) {
      // WHY: Aborted requests (rapid typing) should not clear results from a previous successful search
      if (e && typeof e === 'object' && 'code' in e && e.code === 'ERR_CANCELED') return
      setCategories([])
      setSearched(true)
    } finally {
      setIsSearching(false)
    }
  }, [])

  // WHY: Auto-search categories after 600ms of no typing (3+ chars)
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)

    const trimmed = productInput.trim()
    // WHY: Don't auto-search when input is an Allegro URL — user clicks "Pobierz" instead
    if (trimmed.length < 3 || /allegro\.pl\/oferta\//i.test(trimmed)) return

    debounceRef.current = setTimeout(() => { doSearch(trimmed) }, 600)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [productInput, doSearch])

  // WHY: Cancel in-flight requests on unmount
  useEffect(() => {
    return () => { if (abortRef.current) abortRef.current.abort() }
  }, [])

  const isAllegroUrl = (text: string) => /allegro\.pl\/oferta\//i.test(text.trim())

  const handleResolveUrl = useCallback(async () => {
    const url = productInput.trim()
    if (!isAllegroUrl(url)) return
    setIsResolving(true)
    setResolveError('')
    setCategories([])
    setSelectedCategory(null)
    setSearched(false)
    try {
      const resolved = await resolveAllegroUrl(url)
      setProductInput(resolved.title)
      const cat: AllegroCategory = {
        id: resolved.category_id, name: resolved.category_name,
        path: resolved.category_path, leaf: resolved.leaf,
      }
      setCategories([cat])
      setSelectedCategory(cat)
      setSearched(true)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Nie udało się pobrać danych z Allegro'
      setResolveError(msg)
    } finally {
      setIsResolving(false)
    }
  }, [productInput])

  const handleSearchCategories = () => {
    if (!productInput.trim() || productInput.trim().length < 2) return
    doSearch(productInput.trim())
  }

  // WHY: Single action button — resolve URL or search categories based on input
  const handleAction = () => {
    if (isAllegroUrl(productInput)) {
      handleResolveUrl()
    } else {
      handleSearchCategories()
    }
  }

  const handleReset = () => {
    setCategories([])
    setSelectedCategory(null)
    setSearched(false)
  }

  const handleSubmit = () => {
    if (!selectedCategory) return
    onSubmit(productInput.trim(), selectedCategory.id, selectedCategory.name, selectedCategory.path, marketplace)
  }

  return (
    <div className="space-y-4">
      {/* Marketplace Toggle */}
      <div className="flex gap-2">
        {(['allegro', 'kaufland'] as Marketplace[]).map((mp) => (
          <button
            key={mp}
            onClick={() => setMarketplace(mp)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              marketplace === mp
                ? 'bg-blue-600 text-white'
                : 'bg-[#121212] text-gray-400 hover:text-white border border-gray-700'
            }`}
          >
            {mp === 'allegro' ? 'Allegro' : 'Kaufland'}
          </button>
        ))}
      </div>

      {/* Step 1: Product Input */}
      <Card className="border-gray-800">
        <CardContent className="p-4 space-y-3">
          <label className="text-sm font-medium text-gray-300">Nazwa produktu, tytuł oferty lub link Allegro</label>
          <div className="flex gap-2">
            <Input
              value={productInput}
              onChange={(e) => setProductInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAction()}
              placeholder="np. Samsung Galaxy S24 Ultra 256GB lub link allegro.pl/oferta/..."
              className="flex-1 bg-[#121212] border-gray-700 text-white placeholder:text-gray-500"
              disabled={isLoading}
            />
            <Button
              onClick={handleAction}
              disabled={!productInput.trim() || productInput.trim().length < 2 || isSearching || isResolving || isLoading}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {(isSearching || isResolving) ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : isAllegroUrl(productInput) ? (
                <Link className="h-4 w-4" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              <span className="ml-2 hidden sm:inline">
                {isAllegroUrl(productInput) ? 'Pobierz z Allegro' : 'Szukaj kategorii'}
              </span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {resolveError && (
        <p className="text-sm text-red-400">{resolveError}</p>
      )}

      {/* Step 2: Category Selection */}
      <CategoryList
        categories={categories}
        selectedId={selectedCategory?.id ?? null}
        marketplace={marketplace}
        searched={searched}
        onSelect={setSelectedCategory}
        onReset={handleReset}
      />

      {/* Generate Button */}
      {selectedCategory && (
        <Button
          onClick={handleSubmit}
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generowanie atrybutów...
            </>
          ) : (
            <>Generuj atrybuty dla: {selectedCategory.name}</>
          )}
        </Button>
      )}
    </div>
  )
}
