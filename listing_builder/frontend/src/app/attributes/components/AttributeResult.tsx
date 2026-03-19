// frontend/src/app/attributes/components/AttributeResult.tsx
// Purpose: Editable attribute table with export (CSV, clipboard)
// NOT for: Form logic (AttributeForm.tsx) or history (AttributeHistory.tsx)

'use client'

import { useState } from 'react'
import { Copy, Download, Clock, CheckCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { AttributeRunResponse } from '@/lib/types'

interface AttributeResultProps {
  result: AttributeRunResponse
}

export function AttributeResult({ result }: AttributeResultProps) {
  const [attributes, setAttributes] = useState(result.attributes)
  const [copied, setCopied] = useState(false)

  const requiredCount = attributes.filter((a) => a.required).length
  const filledCount = attributes.filter((a) => a.value !== null && a.value !== '').length

  const updateValue = (index: number, value: string) => {
    const updated = [...attributes]
    updated[index] = { ...updated[index], value: value || null }
    setAttributes(updated)
  }

  const handleCopy = async () => {
    const text = attributes
      .map((a) => `${a.name}\t${a.value ?? ''}`)
      .join('\n')
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleExportCSV = () => {
    // WHY: BOM for Excel to recognize UTF-8 Polish characters
    const bom = '\uFEFF'
    const header = 'Atrybut,Wartość,Wymagany,Typ\n'
    const rows = attributes
      .map((a) => {
        const val = (a.value ?? '').replace(/"/g, '""')
        return `"${a.name}","${val}",${a.required ? 'Tak' : 'Nie'},${a.type}`
      })
      .join('\n')

    const blob = new Blob([bom + header + rows], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `atrybuty-${result.category_name.replace(/\s+/g, '-')}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Card className="border-gray-800">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-white text-lg">{result.category_name}</CardTitle>
            <p className="text-xs text-gray-500 mt-1">{result.category_path}</p>
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {(result.latency_ms / 1000).toFixed(1)}s
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle className="h-3 w-3" />
              {filledCount}/{attributes.length} uzupełnionych
            </span>
          </div>
        </div>
        <div className="flex gap-2 mt-2">
          <Button variant="outline" size="sm" onClick={handleCopy} className="border-gray-700 text-gray-300">
            <Copy className="mr-1 h-3 w-3" />
            {copied ? 'Skopiowano!' : 'Kopiuj'}
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportCSV} className="border-gray-700 text-gray-300">
            <Download className="mr-1 h-3 w-3" />
            CSV
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-left text-xs text-gray-500">
                <th className="px-4 py-2 font-medium">Atrybut</th>
                <th className="px-4 py-2 font-medium">Wartość</th>
                <th className="px-4 py-2 font-medium w-20">Wymagany</th>
                <th className="px-4 py-2 font-medium w-24">Typ</th>
              </tr>
            </thead>
            <tbody>
              {attributes.map((attr, i) => {
                const isMissing = attr.required && (attr.value === null || attr.value === '')
                return (
                  <tr
                    key={`${attr.param_id}-${i}`}
                    className={`border-b border-gray-800/50 ${isMissing ? 'bg-amber-500/5' : ''}`}
                  >
                    <td className="px-4 py-2 text-gray-300">{attr.name}</td>
                    <td className="px-4 py-2">
                      {attr.type === 'DICTIONARY' && attr.options && attr.options.length > 0 ? (
                        <select
                          value={attr.value ?? ''}
                          onChange={(e) => updateValue(i, e.target.value)}
                          className="w-full rounded border border-gray-700 bg-[#121212] px-2 py-1 text-sm text-white"
                        >
                          <option value="">-- wybierz --</option>
                          {attr.options.map((opt) => (
                            <option key={opt.id} value={opt.value}>
                              {opt.value}
                            </option>
                          ))}
                        </select>
                      ) : attr.value === null || attr.value === '' ? (
                        <div className="flex items-center gap-2">
                          <span className="rounded bg-red-500/20 px-1.5 py-0.5 text-[10px] text-red-400">brak</span>
                          <Input
                            value=""
                            onChange={(e) => updateValue(i, e.target.value)}
                            placeholder="Uzupełnij..."
                            className="h-7 bg-[#121212] border-gray-700 text-white text-sm"
                          />
                        </div>
                      ) : (
                        <Input
                          value={attr.value}
                          onChange={(e) => updateValue(i, e.target.value)}
                          className="h-7 bg-[#121212] border-gray-700 text-white text-sm"
                        />
                      )}
                    </td>
                    <td className="px-4 py-2 text-center">
                      {attr.required ? (
                        <span className="rounded bg-amber-500/20 px-1.5 py-0.5 text-[10px] text-amber-400">Tak</span>
                      ) : (
                        <span className="text-xs text-gray-600">Nie</span>
                      )}
                    </td>
                    <td className="px-4 py-2">
                      <span className="rounded bg-gray-800 px-1.5 py-0.5 text-[10px] text-gray-400">{attr.type}</span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
