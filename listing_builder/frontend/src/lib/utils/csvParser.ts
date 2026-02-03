// frontend/src/lib/utils/csvParser.ts
// Purpose: Parse CSV/paste input into batch optimizer products, export results as CSV
// NOT for: API calls or UI rendering

import Papa from 'papaparse'
import type { ParsedBatchProduct, BatchOptimizerResponse } from '../types'

// WHY: CSV columns match the OptimizerRequest fields — keywords are pipe-separated within a cell
interface CSVRow {
  product_title?: string
  brand?: string
  keywords?: string
  product_line?: string
  asin?: string
  category?: string
}

/**
 * Parse CSV text into batch products.
 * Expected columns: product_title, brand, keywords (pipe-separated)
 * Optional: product_line, asin, category
 */
export function parseOptimizerCSV(text: string): ParsedBatchProduct[] {
  const result = Papa.parse<CSVRow>(text, {
    header: true,
    skipEmptyLines: true,
    transformHeader: (h) => h.trim().toLowerCase().replace(/\s+/g, '_'),
  })

  return result.data
    .filter((row) => row.product_title && row.brand && row.keywords)
    .map((row) => ({
      product_title: row.product_title!.trim(),
      brand: row.brand!.trim(),
      keywords: row.keywords!
        .split('|')
        .map((k) => k.trim())
        .filter((k) => k.length > 0),
      product_line: row.product_line?.trim() || undefined,
      asin: row.asin?.trim() || undefined,
      category: row.category?.trim() || undefined,
    }))
}

/**
 * Parse pasted text — one product per line, pipe-separated fields.
 * Format: title|brand|keyword1,keyword2,keyword3
 */
export function parsePasteText(text: string): ParsedBatchProduct[] {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => {
      const parts = line.split('|').map((p) => p.trim())
      // WHY: Minimum 3 parts — title, brand, and at least one keyword
      if (parts.length < 3) return null

      return {
        product_title: parts[0],
        brand: parts[1],
        keywords: parts[2]
          .split(',')
          .map((k) => k.trim())
          .filter((k) => k.length > 0),
      }
    })
    .filter((p): p is ParsedBatchProduct => p !== null && p.keywords.length > 0)
}

/**
 * Export batch results as a downloadable CSV file.
 * Includes title, bullets, description, backend keywords, and coverage score.
 */
export function exportResultsCSV(response: BatchOptimizerResponse): void {
  const rows = response.results
    .filter((r) => r.status === 'completed' && r.result)
    .map((r) => {
      const res = r.result!
      return {
        product_title: r.product_title,
        generated_title: res.listing.title,
        bullet_1: res.listing.bullet_points[0] || '',
        bullet_2: res.listing.bullet_points[1] || '',
        bullet_3: res.listing.bullet_points[2] || '',
        bullet_4: res.listing.bullet_points[3] || '',
        bullet_5: res.listing.bullet_points[4] || '',
        description: res.listing.description,
        backend_keywords: res.listing.backend_keywords,
        coverage_pct: res.scores.coverage_pct,
        compliance_status: res.scores.compliance_status,
      }
    })

  const csv = Papa.unparse(rows)
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `optimized_listings_${Date.now()}.csv`
  link.click()
  URL.revokeObjectURL(url)
}
