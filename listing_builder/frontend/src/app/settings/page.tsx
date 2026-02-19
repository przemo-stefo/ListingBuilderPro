// frontend/src/app/settings/page.tsx
// Purpose: Settings page — General config, Notifications, Data & Export (Marketplace connections → /integrations)
// NOT for: API logic or data fetching (handled by hooks/useSettings.ts)

'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Settings as SettingsIcon, Link as LinkIcon, Bell, Download, Save, Cpu } from 'lucide-react'
import { FaqSection } from '@/components/ui/FaqSection'

const SETTINGS_FAQ = [
  { question: 'Jak zmienić domyślny marketplace?', answer: 'W sekcji "Ustawienia ogólne" wybierz nowy marketplace z listy i kliknij "Zapisz". Wszystkie nowe optymalizacje będą domyślnie tworzone dla wybranego rynku.' },
  { question: 'Jak połączyć marketplace?', answer: 'Przejdź do strony Integracje w menu głównym. Tam możesz połączyć konto przez OAuth (Amazon, Allegro, eBay) i zarządzać wszystkimi połączeniami w jednym miejscu.' },
  { question: 'Jakie powiadomienia są dostępne?', answer: 'Możesz włączyć alerty email, powiadomienia o niskim stanie magazynowym, zmianach cen konkurencji i ostrzeżeniach o zgodności (compliance). Każdy typ można włączać/wyłączać niezależnie.' },
  { question: 'Jak zmienić format eksportu?', answer: 'W sekcji "Dane i eksport" wybierz preferowany format (CSV, JSON, Excel). Wszystkie pobrania z systemu będą używały wybranego formatu.' },
  { question: 'Co to jest "Model AI" i po co mi to?', answer: 'Model AI to silnik sztucznej inteligencji generujacy listingi. Domyslnie uzywa Groq (Llama 3.3 70B) — jest darmowy i wystarczajacy w wiekszosci przypadkow. Jesli chcesz wyzsza jakosc (np. Gemini Pro), mozesz podac swoj klucz API.' },
  { question: 'Skad wziac klucz API Gemini lub OpenAI?', answer: 'Gemini: wejdz na aistudio.google.com → kliknij "Get API key" → skopiuj klucz. OpenAI: wejdz na platform.openai.com → API keys → "Create new secret key". Klucze sa platne wg zuzycia — sprawdz cennik danego providera.' },
  { question: 'Czy Groq jest naprawde darmowy?', answer: 'Tak! Groq jest wliczony w cene i nie wymaga klucza API. Uzywa modelu Llama 3.3 70B Versatile — wystarczajaco dobrego do wiekszosci listingow. Platne providery (Gemini Pro, OpenAI) moga dawac lepsza jakosc tekstu.' },
  { question: 'Co sie stanie jesli moj klucz API jest nieprawidlowy?', answer: 'System automatycznie przelacza na Groq (darmowy) jesli Twoj klucz API nie zadziala. Zobaczysz wynik wygenerowany przez Groq zamiast wybranego providera. Sprawdz klucz w Ustawieniach i sprobuj ponownie.' },
]
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useSettings, useUpdateSettings } from '@/lib/hooks/useSettings'
import type {
  MarketplaceId,
  NotificationSettings,
  ExportFormat,
  SyncFrequency,
  LLMProvider,
} from '@/lib/types'

// WHY: Provider options for the AI Model card — Groq is free (included), others need user's key
const LLM_PROVIDERS: { id: LLMProvider; label: string; desc: string }[] = [
  { id: 'groq', label: 'Groq', desc: 'Llama 3.3 70B (w cenie)' },
  { id: 'gemini_flash', label: 'Gemini Flash', desc: 'Szybki, tani (Twoj klucz)' },
  { id: 'gemini_pro', label: 'Gemini Pro', desc: 'Najlepsza jakosc (Twoj klucz)' },
  { id: 'openai', label: 'OpenAI', desc: 'GPT-4o Mini (Twoj klucz)' },
]

const MARKETPLACE_OPTIONS: { id: MarketplaceId; label: string }[] = [
  { id: 'amazon', label: 'Amazon' },
  { id: 'ebay', label: 'eBay' },
  { id: 'walmart', label: 'Walmart' },
  { id: 'shopify', label: 'Shopify' },
  { id: 'allegro', label: 'Allegro' },
]

const TIMEZONE_OPTIONS = [
  'America/New_York',
  'America/Chicago',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Warsaw',
]

const EXPORT_OPTIONS: { id: ExportFormat; label: string }[] = [
  { id: 'csv', label: 'CSV' },
  { id: 'json', label: 'JSON' },
  { id: 'excel', label: 'Excel' },
]

const SYNC_OPTIONS: { id: SyncFrequency; label: string }[] = [
  { id: 'manual', label: 'Ręczna' },
  { id: '1h', label: '1h' },
  { id: '6h', label: '6h' },
  { id: '12h', label: '12h' },
  { id: '24h', label: '24h' },
]

// WHY: Skeleton shows while data loads — same pattern as other pages
function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="h-48 animate-pulse rounded-lg border border-gray-800 bg-[#121212]"
        />
      ))}
    </div>
  )
}

export default function SettingsPage() {
  const { data, isLoading, isError, refetch } = useSettings()
  const updateSettings = useUpdateSettings()

  // Local state for each section (populated from server data)
  const [storeName, setStoreName] = useState('')
  const [defaultMarketplace, setDefaultMarketplace] = useState<MarketplaceId>('amazon')
  const [timezone, setTimezone] = useState('America/New_York')
  const [notifications, setNotifications] = useState<NotificationSettings>({
    email_alerts: true,
    low_stock_alerts: true,
    competitor_price_changes: false,
    compliance_warnings: true,
  })
  const [exportFormat, setExportFormat] = useState<ExportFormat>('csv')
  const [syncFrequency, setSyncFrequency] = useState<SyncFrequency>('6h')
  const [llmProvider, setLlmProvider] = useState<LLMProvider>('groq')
  // WHY: Store per-provider API keys locally. Groq doesn't need one (our key).
  const [llmKeys, setLlmKeys] = useState<Record<string, string>>({})

  // WHY: Populate local state when server data arrives or changes
  useEffect(() => {
    if (!data) return
    setStoreName(data.general.store_name)
    setDefaultMarketplace(data.general.default_marketplace)
    setTimezone(data.general.timezone)
    setNotifications(data.notifications)
    setExportFormat(data.data_export.default_export_format)
    setSyncFrequency(data.data_export.auto_sync_frequency)
    if (data.llm) {
      setLlmProvider(data.llm.default_provider)
      const keys: Record<string, string> = {}
      for (const [pname, pconf] of Object.entries(data.llm.providers || {})) {
        keys[pname] = pconf?.api_key || ''
      }
      setLlmKeys(keys)
    }
  }, [data])

  if (isLoading) return <LoadingSkeleton />

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <p className="text-gray-400">Nie udało się załadować ustawień</p>
        <Button variant="outline" onClick={() => refetch()}>
          Ponów
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Ustawienia</h1>
        <p className="text-sm text-gray-400">
          Konfiguracja sklepu, połączenia z marketplace&apos;ami i preferencje. Ustaw domyślny rynek, powiadomienia i format eksportu.
        </p>
      </div>

      {/* Card 1 — Ustawienia ogolne */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <SettingsIcon className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Ustawienia ogólne</CardTitle>
          </div>
          <CardDescription>Podstawowa konfiguracja sklepu</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Nazwa sklepu */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">Nazwa sklepu</label>
            <Input
              value={storeName}
              onChange={(e) => setStoreName(e.target.value)}
              placeholder="Nazwa Twojego sklepu"
            />
          </div>

          {/* Domyslny marketplace */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">Domyślny marketplace</label>
            <div className="flex flex-wrap gap-2">
              {MARKETPLACE_OPTIONS.map((mp) => (
                <Button
                  key={mp.id}
                  variant={defaultMarketplace === mp.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setDefaultMarketplace(mp.id)}
                >
                  {mp.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Strefa czasowa */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">Strefa czasowa</label>
            <div className="flex flex-wrap gap-2">
              {TIMEZONE_OPTIONS.map((tz) => (
                <Button
                  key={tz}
                  variant={timezone === tz ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTimezone(tz)}
                >
                  {tz.replace('_', ' ')}
                </Button>
              ))}
            </div>
          </div>

          {/* Zapisz */}
          <div className="flex justify-end">
            <Button
              onClick={() =>
                updateSettings.mutate({
                  general: {
                    store_name: storeName,
                    default_marketplace: defaultMarketplace,
                    timezone,
                  },
                })
              }
              disabled={updateSettings.isPending}
            >
              <Save className="mr-2 h-4 w-4" />
              Zapisz
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Card — Model AI */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Model AI</CardTitle>
          </div>
          <CardDescription>Wybierz silnik AI do generowania listingow. Groq (Llama 3.3) jest darmowy i wliczony w cene. Gemini i OpenAI wymagaja Twojego klucza API.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-2 block text-sm text-gray-400">Domyslny provider</label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {LLM_PROVIDERS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setLlmProvider(p.id)}
                  className={`rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                    llmProvider === p.id
                      ? 'border-white bg-white/5 text-white'
                      : 'border-gray-800 text-gray-400 hover:border-gray-600 hover:text-white'
                  }`}
                >
                  <span className="font-medium">{p.label}</span>
                  <span className="block text-[10px] text-gray-500">{p.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* WHY: Show API key input only for non-Groq providers */}
          {llmProvider !== 'groq' && (
            <div>
              <label className="mb-1 block text-sm text-gray-400">
                Klucz API ({LLM_PROVIDERS.find((p) => p.id === llmProvider)?.label})
              </label>
              <Input
                type="password"
                value={llmKeys[llmProvider] || ''}
                onChange={(e) =>
                  setLlmKeys((prev) => ({ ...prev, [llmProvider]: e.target.value }))
                }
                placeholder="Wklej swoj klucz API"
              />
              <p className="mt-1 text-[10px] text-gray-500">
                Klucz jest szyfrowany i nigdy nie wyswietlany w pelni.
              </p>
            </div>
          )}

          <div className="flex justify-end">
            <Button
              onClick={() => {
                const providers: Record<string, { api_key: string }> = {}
                for (const [pname, key] of Object.entries(llmKeys)) {
                  if (key) providers[pname] = { api_key: key }
                }
                updateSettings.mutate({
                  llm: { default_provider: llmProvider, providers },
                })
              }}
              disabled={updateSettings.isPending}
            >
              <Save className="mr-2 h-4 w-4" />
              Zapisz
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* WHY: Marketplace connections moved to /integrations — link only */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <LinkIcon className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Połączenia z marketplace&apos;ami</CardTitle>
          </div>
          <CardDescription>Zarządzaj OAuth i API marketplace&apos;ów w jednym miejscu</CardDescription>
        </CardHeader>
        <CardContent>
          <Link
            href="/integrations"
            className="inline-flex items-center gap-2 rounded-lg border border-gray-700 bg-white/5 px-4 py-2.5 text-sm font-medium text-white hover:bg-white/10 transition-colors"
          >
            Zarządzaj w Integracje →
          </Link>
        </CardContent>
      </Card>

      {/* Card 3 — Preferencje powiadomien */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Preferencje powiadomień</CardTitle>
          </div>
          <CardDescription>Wybierz jakie alerty chcesz otrzymywać</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {([
            {
              key: 'email_alerts' as const,
              label: 'Alerty email',
              desc: 'Otrzymuj powiadomienia email o ważnych zdarzeniach',
            },
            {
              key: 'low_stock_alerts' as const,
              label: 'Alerty niskiego stanu',
              desc: 'Powiadomienie gdy stan magazynowy spadnie poniżej minimum',
            },
            {
              key: 'competitor_price_changes' as const,
              label: 'Zmiany cen konkurencji',
              desc: 'Alert gdy konkurencja zmieni ceny',
            },
            {
              key: 'compliance_warnings' as const,
              label: 'Ostrzeżenia zgodności',
              desc: 'Powiadomienia o problemach ze zgodnościami listingów',
            },
          ]).map((item) => (
            <div
              key={item.key}
              className="flex items-center justify-between rounded-lg border border-gray-800 bg-[#1A1A1A] p-4"
            >
              <div>
                <p className="text-sm font-medium text-white">{item.label}</p>
                <p className="text-xs text-gray-400">{item.desc}</p>
              </div>
              <Button
                size="sm"
                variant={notifications[item.key] ? 'default' : 'outline'}
                onClick={() =>
                  setNotifications((prev) => ({
                    ...prev,
                    [item.key]: !prev[item.key],
                  }))
                }
              >
                {notifications[item.key] ? 'WL.' : 'WYL.'}
              </Button>
            </div>
          ))}

          <div className="flex justify-end">
            <Button
              onClick={() => updateSettings.mutate({ notifications })}
              disabled={updateSettings.isPending}
            >
              <Save className="mr-2 h-4 w-4" />
              Zapisz
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Card 4 — Dane i eksport */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Download className="h-5 w-5 text-gray-400" />
            <CardTitle className="text-lg">Dane i eksport</CardTitle>
          </div>
          <CardDescription>Skonfiguruj formaty eksportu i harmonogram synchronizacji</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Format eksportu */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">Format eksportu</label>
            <div className="flex gap-2">
              {EXPORT_OPTIONS.map((opt) => (
                <Button
                  key={opt.id}
                  variant={exportFormat === opt.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setExportFormat(opt.id)}
                >
                  {opt.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Częstotliwość synchronizacji */}
          <div>
            <label className="mb-1 block text-sm text-gray-400">Częstotliwość auto-synchronizacji</label>
            <div className="flex gap-2">
              {SYNC_OPTIONS.map((opt) => (
                <Button
                  key={opt.id}
                  variant={syncFrequency === opt.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSyncFrequency(opt.id)}
                >
                  {opt.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Zapisz */}
          <div className="flex justify-end">
            <Button
              onClick={() =>
                updateSettings.mutate({
                  data_export: {
                    default_export_format: exportFormat,
                    auto_sync_frequency: syncFrequency,
                  },
                })
              }
              disabled={updateSettings.isPending}
            >
              <Save className="mr-2 h-4 w-4" />
              Zapisz
            </Button>
          </div>
        </CardContent>
      </Card>

      <FaqSection
        title="Najczęściej zadawane pytania"
        subtitle="Konfiguracja i ustawienia"
        items={SETTINGS_FAQ}
      />
    </div>
  )
}
