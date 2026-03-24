// frontend/src/app/attributes/components/AttributeForm.tsx
// Purpose: 2-step form — product input → category selector → generate
// NOT for: Result display (AttributeResult.tsx) or history (AttributeHistory.tsx)

'use client'

import { useState, useRef, useEffect } from 'react'
import { Search, Loader2, ChevronRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { searchCategories } from '@/lib/api/attributes'

type Marketplace = 'allegro' | 'kaufland'

interface AllegroCategory {
  id: string
  name: string
  path: string
  leaf: boolean
}

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
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const doSearch = async (query: string) => {
    setIsSearching(true)
    setSelectedCategory(null)
    setSearched(false)
    try {
      const data = await searchCategories(query)
      setCategories(data.categories || [])
      setSearched(true)
    } catch {
      setCategories([])
      setSearched(true)
    } finally {
      setIsSearching(false)
    }
  }

  // WHY: Auto-search categories after 600ms of no typing (3+ chars)
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)

    const trimmed = productInput.trim()
    if (trimmed.length < 3) return

    debounceRef.current = setTimeout(() => { doSearch(trimmed) }, 600)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [productInput])

  const handleSearchCategories = () => {
    if (!productInput.trim() || productInput.trim().length < 2) return
    doSearch(productInput.trim())
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
          <label className="text-sm font-medium text-gray-300">Nazwa produktu lub tytuł oferty</label>
          <div className="flex gap-2">
            <Input
              value={productInput}
              onChange={(e) => setProductInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearchCategories()}
              placeholder="np. Samsung Galaxy S24 Ultra 256GB"
              className="flex-1 bg-[#121212] border-gray-700 text-white placeholder:text-gray-500"
              disabled={isLoading}
            />
            <Button
              onClick={handleSearchCategories}
              disabled={!productInput.trim() || productInput.trim().length < 2 || isSearching || isLoading}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              <span className="ml-2 hidden sm:inline">Szukaj kategorii</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Step 2: Category Selection */}
      {searched && categories.length > 0 && (
        <Card className="border-gray-800">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-300">Wybierz kategorię {marketplace === 'kaufland' ? 'Kaufland' : 'Allegro'}</label>
              <button onClick={handleReset} className="text-xs text-gray-500 hover:text-gray-300">Zmień</button>
            </div>
            <div className="space-y-2">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat)}
                  className={`w-full rounded-lg border p-3 text-left transition-colors ${
                    selectedCategory?.id === cat.id
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-gray-700 bg-[#121212] hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium text-white">{cat.name}</span>
                      {cat.leaf && (
                        <span className="ml-2 rounded bg-green-500/20 px-1.5 py-0.5 text-[10px] text-green-400">leaf</span>
                      )}
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-500" />
                  </div>
                  <p className="mt-1 text-xs text-gray-500">{cat.path}</p>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {searched && categories.length === 0 && (
        <Card className="border-gray-800">
          <CardContent className="p-4">
            <p className="text-sm text-gray-400">Nie znaleziono kategorii. Spróbuj inną nazwę produktu.</p>
          </CardContent>
        </Card>
      )}

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
