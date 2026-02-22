// frontend/src/app/products/import/components/BatchImport.tsx
// Purpose: Batch product import from CSV (Allegro export) or pasted data
// NOT for: Single product import or optimization

'use client'

import { useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useToast } from '@/lib/hooks/useToast'
import { cn } from '@/lib/utils'
import { FileUp, Clipboard, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import Papa from 'papaparse'
import { apiRequest } from '@/lib/api/client'
import { MARKETPLACES, COLUMN_MAP, MAX_BATCH_SIZE } from '../constants'
import type { ParsedProduct } from '../constants'
import PreviewTable from './PreviewTable'

export default function BatchImport() {
  const router = useRouter()
  const { toast } = useToast()
  const fileRef = useRef<HTMLInputElement>(null)

  const [source, setSource] = useState('allegro')
  const [products, setProducts] = useState<ParsedProduct[]>([])
  const [pasteText, setPasteText] = useState('')
  const [isImporting, setIsImporting] = useState(false)
  const [result, setResult] = useState<{ success: number; failed: number } | null>(null)

  // WHY: Auto-detect CSV columns using the COLUMN_MAP lookup table
  const parseCSVData = useCallback((text: string) => {
    const parsed = Papa.parse<Record<string, string>>(text, {
      header: true,
      skipEmptyLines: true,
      transformHeader: (h) => h.trim().toLowerCase(),
    })

    const mapped: ParsedProduct[] = []
    for (const [idx, row] of parsed.data.entries()) {
      if (mapped.length >= MAX_BATCH_SIZE) break
      const fields: Record<string, string | number | undefined> = {}
      for (const [csvCol, value] of Object.entries(row)) {
        const field = COLUMN_MAP[csvCol]
        if (field && value?.trim()) {
          fields[field] = field === 'price' ? parseFloat(value.replace(',', '.')) : value.trim()
        }
      }
      if (!fields.title) continue
      // WHY: Use String() + truthiness check to avoid storing "undefined" text in DB
      mapped.push({
        title: String(fields.title),
        price: typeof fields.price === 'number' && !isNaN(fields.price) ? fields.price : undefined,
        source_id: fields.source_id ? String(fields.source_id) : `import-${idx + 1}`,
        category: fields.category ? String(fields.category) : undefined,
        brand: fields.brand ? String(fields.brand) : undefined,
        description: fields.description ? String(fields.description) : undefined,
        source_url: fields.source_url ? String(fields.source_url) : undefined,
        currency: fields.currency ? String(fields.currency) : undefined,
      })
    }

    // WHY: Deduplicate by source_id — prevents crash when CSV has duplicate rows
    const seen = new Set<string>()
    const deduped = mapped.filter(p => {
      if (seen.has(p.source_id)) return false
      seen.add(p.source_id)
      return true
    })
    const dupeCount = mapped.length - deduped.length

    // WHY: If >50% of products got fallback "import-N" IDs, column mapping likely failed
    const unmappedCount = deduped.filter(p => p.source_id.startsWith('import-')).length
    const unmappedPct = deduped.length > 0 ? unmappedCount / deduped.length : 0

    setProducts(deduped)
    const total = parsed.data.length
    if (deduped.length === 0) {
      toast({ title: 'Brak danych', description: 'Nie znaleziono produktów. Sprawdź format CSV.', variant: 'destructive' })
    } else {
      if (dupeCount > 0) {
        toast({ title: `Usunięto ${dupeCount} duplikatów`, description: `Pozostało ${deduped.length} unikalnych produktów` })
      }
      if (unmappedPct > 0.5) {
        toast({
          title: 'Brak kolumny ID',
          description: 'Większość produktów nie ma rozpoznanego ID. Sprawdź nagłówki CSV (np. "numer oferty", "asin", "item number").',
          variant: 'destructive',
        })
      }
      const extra = total > MAX_BATCH_SIZE ? ` (limit ${MAX_BATCH_SIZE}, pominięto ${total - MAX_BATCH_SIZE})` : ''
      toast({ title: `Znaleziono ${deduped.length} produktów${extra}`, description: 'Sprawdź podgląd i kliknij Importuj' })
    }
  }, [toast])

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    // WHY: 10MB limit prevents browser freeze on huge files
    if (file.size > 10 * 1024 * 1024) {
      toast({ title: 'Plik za duży', description: 'Maksymalny rozmiar: 10 MB', variant: 'destructive' })
      return
    }
    const reader = new FileReader()
    reader.onload = (ev) => parseCSVData(ev.target?.result as string)
    reader.readAsText(file, 'utf-8')
    // WHY: Reset input so same file can be re-uploaded after changes
    e.target.value = ''
  }

  const handleImport = async () => {
    if (products.length === 0) return
    setIsImporting(true)
    setResult(null)

    try {
      const payload = products.map((p) => ({
        source_platform: source,
        source_id: p.source_id,
        title: p.title,
        price: p.price ?? null,
        category: p.category ?? null,
        brand: p.brand ?? null,
        description: p.description ?? null,
        source_url: p.source_url ?? null,
        currency: p.currency || 'PLN',
      }))

      const res = await apiRequest<{ success_count: number; failed_count: number; job_id: number }>(
        'post', `/import/batch?source=${encodeURIComponent(source)}`, payload
      )
      if (res.error) throw new Error(res.error)

      setResult({ success: res.data!.success_count, failed: res.data!.failed_count })
      toast({
        title: 'Import zakończony',
        description: `${res.data!.success_count} produktów zaimportowano${res.data!.failed_count > 0 ? `, ${res.data!.failed_count} błędów` : ''}`,
      })
    } catch (err) {
      toast({ title: 'Błąd importu', description: (err as Error).message, variant: 'destructive' })
    } finally {
      setIsImporting(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Source marketplace */}
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5">
        <label className="text-sm font-medium text-white mb-3 block">Skąd importujesz?</label>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {MARKETPLACES.map((mp) => (
            <button key={mp.value} type="button" onClick={() => setSource(mp.value)}
              className={cn(
                'flex items-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-medium transition-colors',
                source === mp.value
                  ? 'border-white/20 bg-white/10 text-white'
                  : 'border-gray-800 text-gray-400 hover:border-gray-600 hover:text-white'
              )}>
              <span>{mp.flag}</span> {mp.label}
            </button>
          ))}
        </div>
      </div>

      {/* CSV upload + paste area */}
      <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5 space-y-4">
        <div className="flex gap-3">
          <button type="button" onClick={() => fileRef.current?.click()}
            className="flex items-center gap-2 rounded-lg border border-dashed border-gray-600 px-4 py-3 text-sm text-gray-400 hover:border-white hover:text-white transition-colors">
            <FileUp className="h-4 w-4" /> Wgraj CSV
          </button>
          <input ref={fileRef} type="file" accept=".csv,.tsv,.txt" onChange={handleFileUpload} className="hidden" />
          <span className="flex items-center text-xs text-gray-600">lub wklej dane poniżej</span>
        </div>
        <textarea
          value={pasteText}
          onChange={(e) => setPasteText(e.target.value)}
          placeholder={`Wklej CSV z nagłówkami, np.:\ntytuł,cena,numer oferty,marka\nBudzik LED,29.99,12345,BrandX\nKabel USB-C,19.99,67890,TechY`}
          rows={5}
          className="w-full rounded-lg border border-gray-700 bg-[#121212] px-4 py-3 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20 font-mono"
        />
        {pasteText.trim() && (
          <button type="button" onClick={() => parseCSVData(pasteText)}
            className="flex items-center gap-2 rounded-lg bg-white/10 px-4 py-2 text-sm text-white hover:bg-white/20 transition-colors">
            <Clipboard className="h-4 w-4" /> Parsuj wklejone dane
          </button>
        )}
        <p className="text-xs text-gray-600">
          Kolumny: tytuł, cena, numer oferty, marka, kategoria, opis, url.
          Polskie i angielskie nagłówki rozpoznawane automatycznie. Limit: {MAX_BATCH_SIZE} produktów.
        </p>
      </div>

      {/* Preview table */}
      {products.length > 0 && (
        <PreviewTable
          products={products}
          onRemove={(idx) => setProducts(products.filter((_, i) => i !== idx))}
          onClear={() => setProducts([])}
        />
      )}

      {/* Result */}
      {result && (
        <div className="rounded-xl border border-gray-800 bg-[#1A1A1A] p-5 flex items-center gap-4">
          <CheckCircle2 className="h-6 w-6 text-green-400 shrink-0" />
          <div>
            <p className="text-sm text-white font-medium">Zaimportowano {result.success} produktów</p>
            {result.failed > 0 && (
              <p className="text-xs text-red-400 flex items-center gap-1 mt-1">
                <XCircle className="h-3.5 w-3.5" /> {result.failed} błędów
              </p>
            )}
          </div>
          <button onClick={() => router.push('/products')}
            className="ml-auto rounded-lg bg-white px-4 py-2 text-sm font-medium text-black hover:bg-gray-200 transition-colors">
            Zobacz produkty
          </button>
        </div>
      )}

      {/* Import button */}
      {products.length > 0 && !result && (
        <button onClick={handleImport} disabled={isImporting}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-white px-4 py-3 text-sm font-medium text-black hover:bg-gray-200 transition-colors disabled:opacity-50">
          {isImporting ? (
            <><Loader2 className="h-4 w-4 animate-spin" /> Importowanie...</>
          ) : (
            <><FileUp className="h-4 w-4" /> Importuj {products.length} produktów z {source}</>
          )}
        </button>
      )}
    </div>
  )
}
