// frontend/src/app/validator/components/ValidatorForm.tsx
// Purpose: Input form for product validation — name/ASIN/URL + marketplace selector
// NOT for: Displaying results (ValidatorResult.tsx) or history (ValidatorHistory.tsx)

'use client'

import { useState } from 'react'
import { Loader2, Search } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

interface ValidatorFormProps {
  onSubmit: (productInput: string, marketplace: string) => void
  isLoading: boolean
}

const MARKETPLACES = [
  { value: 'amazon', label: 'Amazon' },
  { value: 'allegro', label: 'Allegro' },
  { value: 'both', label: 'Oba' },
]

export function ValidatorForm({ onSubmit, isLoading }: ValidatorFormProps) {
  const [productInput, setProductInput] = useState('')
  const [marketplace, setMarketplace] = useState('amazon')

  const canSubmit = productInput.trim().length >= 2 && !isLoading

  const handleSubmit = () => {
    if (!canSubmit) return
    onSubmit(productInput.trim(), marketplace)
  }

  return (
    <Card className="border-gray-800">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">Sprawdź produkt</CardTitle>
        <CardDescription>Wpisz nazwę produktu, ASIN lub URL — AI oceni potencjał sprzedażowy</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="mb-1 block text-sm text-gray-400">
            Produkt <span className="text-red-400">*</span>
          </label>
          <Input
            value={productInput}
            onChange={(e) => setProductInput(e.target.value)}
            placeholder="np. prasa do czosnku, B0XXXXXX, lub link Amazon/Allegro"
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          />
        </div>

        {/* WHY: Radio buttons for marketplace — simple, no dropdown overhead */}
        <div>
          <label className="mb-2 block text-sm text-gray-400">Marketplace</label>
          <div className="flex gap-3">
            {MARKETPLACES.map((mp) => (
              <button
                key={mp.value}
                onClick={() => setMarketplace(mp.value)}
                className={cn(
                  'rounded-lg border px-4 py-2 text-sm transition-colors',
                  marketplace === mp.value
                    ? 'border-blue-500 bg-blue-500/10 text-blue-400'
                    : 'border-gray-800 text-gray-400 hover:border-gray-600'
                )}
              >
                {mp.label}
              </button>
            ))}
          </div>
        </div>

        <Button onClick={handleSubmit} disabled={!canSubmit} size="lg" className="w-full">
          {isLoading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Search className="mr-2 h-4 w-4" />
          )}
          {isLoading ? 'Analizuję...' : 'Analizuj produkt'}
        </Button>
      </CardContent>
    </Card>
  )
}
