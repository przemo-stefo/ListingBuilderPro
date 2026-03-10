// frontend/src/app/optimize/components/TargetModeCard.tsx
// Purpose: Marketplace, optimization mode, account type, and LLM provider selection
// NOT for: Form submission or result display

import { Target, Zap } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import type { LLMProvider } from '@/lib/types'

const LLM_PROVIDERS: { id: LLMProvider; label: string; hint: string; needsKey: boolean }[] = [
  { id: 'groq', label: 'Groq (w cenie)', hint: 'Llama 3.3 70B — darmowy', needsKey: false },
  { id: 'beast', label: 'Beast AI', hint: 'Qwen3 235B — unlimited', needsKey: false },
  { id: 'gemini_flash', label: 'Gemini Flash', hint: 'Szybki i tani', needsKey: true },
  { id: 'gemini_pro', label: 'Gemini Pro', hint: 'Najlepsza jakosc', needsKey: true },
  { id: 'openai', label: 'OpenAI', hint: 'GPT-4o Mini', needsKey: true },
]

const MARKETPLACES = [
  { id: 'amazon_de', name: 'Amazon DE', flag: 'DE' },
  { id: 'amazon_us', name: 'Amazon US', flag: 'US' },
  { id: 'amazon_pl', name: 'Amazon PL', flag: 'PL' },
  { id: 'ebay_de', name: 'eBay DE', flag: 'DE' },
  { id: 'kaufland', name: 'Kaufland', flag: 'DE' },
]

interface TargetModeCardProps {
  marketplace: string
  setMarketplace: (v: string) => void
  mode: 'aggressive' | 'standard'
  setMode: (v: 'aggressive' | 'standard') => void
  accountType: 'seller' | 'vendor'
  setAccountType: (v: 'seller' | 'vendor') => void
  llmProvider: LLMProvider
  setLlmProvider: (v: LLMProvider) => void
  inlineLlmKey: string
  setInlineLlmKey: (v: string) => void
  isPremium: boolean
  hasSavedKey: boolean
}

export { LLM_PROVIDERS, MARKETPLACES }

export function TargetModeCard({
  marketplace, setMarketplace,
  mode, setMode,
  accountType, setAccountType,
  llmProvider, setLlmProvider,
  inlineLlmKey, setInlineLlmKey,
  isPremium, hasSavedKey,
}: TargetModeCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Target className="h-5 w-5 text-gray-400" />
          <CardTitle className="text-lg">Cel i tryb</CardTitle>
        </div>
        <CardDescription>Wybierz marketplace, tryb optymalizacji, typ konta i model AI</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Marketplace */}
        <div>
          <label className="mb-2 block text-sm text-gray-400">Marketplace</label>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
            {MARKETPLACES.map((mp) => {
              const isAmazon = mp.id.startsWith('amazon')
              const isLocked = !isPremium && !isAmazon
              return (
                <button
                  key={mp.id}
                  onClick={() => !isLocked && setMarketplace(mp.id)}
                  disabled={isLocked}
                  title={isLocked ? 'Dostepne w Premium' : undefined}
                  className={cn(
                    'rounded-lg border px-3 py-2 text-sm transition-colors relative',
                    isLocked
                      ? 'border-gray-800 text-gray-600 cursor-not-allowed opacity-50'
                      : marketplace === mp.id
                        ? 'border-white bg-white/5 text-white'
                        : 'border-gray-800 text-gray-400 hover:border-gray-600 hover:text-white'
                  )}
                >
                  <span className="mr-1 text-xs">{mp.flag}</span>
                  {mp.name}
                  {isLocked && <span className="ml-1 text-[10px] text-amber-400">PRO</span>}
                </button>
              )
            })}
          </div>
        </div>

        {/* Mode */}
        <div>
          <label className="mb-2 block text-sm text-gray-400">Tryb optymalizacji</label>
          <div className="flex gap-2">
            <button
              onClick={() => setMode('aggressive')}
              className={cn(
                'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors',
                mode === 'aggressive' ? 'border-white bg-white/5 text-white' : 'border-gray-800 text-gray-400 hover:border-gray-600'
              )}
            >
              <Zap className="h-4 w-4" /> Agresywny
              <span className="text-[10px] text-gray-500">96%+ pokrycie</span>
            </button>
            <button
              onClick={() => setMode('standard')}
              className={cn(
                'flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition-colors',
                mode === 'standard' ? 'border-white bg-white/5 text-white' : 'border-gray-800 text-gray-400 hover:border-gray-600'
              )}
            >
              <Target className="h-4 w-4" /> Standardowy
              <span className="text-[10px] text-gray-500">82%+ pokrycie</span>
            </button>
          </div>
        </div>

        {/* Account type */}
        <div>
          <label className="mb-2 block text-sm text-gray-400">Typ konta Amazon</label>
          <div className="flex gap-2">
            {(['seller', 'vendor'] as const).map((type) => (
              <button
                key={type}
                onClick={() => setAccountType(type)}
                className={cn(
                  'rounded-lg border px-4 py-2 text-sm transition-colors',
                  accountType === type ? 'border-white bg-white/5 text-white' : 'border-gray-800 text-gray-400 hover:border-gray-600'
                )}
              >
                {type === 'seller' ? 'Seller' : 'Vendor'}
                <span className="ml-1 text-[10px] text-gray-500">{type === 'seller' ? '5 bulletow' : '10 bulletow'}</span>
              </button>
            ))}
          </div>
        </div>

        {/* LLM Provider */}
        <div>
          <label className="mb-1 block text-sm text-gray-400">Model AI</label>
          <p className="mb-2 text-[10px] text-gray-500">Silnik AI generujacy listing. Groq jest darmowy. Inne wymagaja klucza API (zapisz go w Ustawieniach).</p>
          <div className="flex flex-wrap gap-2">
            {LLM_PROVIDERS.map((p) => (
              <button
                key={p.id}
                onClick={() => { setLlmProvider(p.id); setInlineLlmKey('') }}
                title={p.hint}
                className={cn(
                  'rounded-lg border px-3 py-1.5 text-sm transition-colors',
                  llmProvider === p.id ? 'border-white bg-white/5 text-white' : 'border-gray-800 text-gray-400 hover:border-gray-600'
                )}
              >
                {p.label}
                <span className="ml-1 text-[9px] text-gray-600">{p.hint}</span>
              </button>
            ))}
          </div>
          {LLM_PROVIDERS.find((p) => p.id === llmProvider)?.needsKey && !hasSavedKey && (
            <div className="mt-2">
              <Input
                type="password"
                value={inlineLlmKey}
                onChange={(e) => setInlineLlmKey(e.target.value)}
                placeholder="Wklej klucz API (lub zapisz w Ustawieniach)"
                className="text-sm"
              />
            </div>
          )}
          {LLM_PROVIDERS.find((p) => p.id === llmProvider)?.needsKey && hasSavedKey && (
            <p className="mt-1 text-[10px] text-gray-500">Uzyje klucza zapisanego w Ustawieniach</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
