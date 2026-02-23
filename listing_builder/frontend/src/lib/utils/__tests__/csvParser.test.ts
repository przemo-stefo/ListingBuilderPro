// frontend/src/lib/utils/__tests__/csvParser.test.ts
// Purpose: Tests for CSV and paste-text parsers
// NOT for: Export functionality (requires DOM)

import { describe, it, expect } from 'vitest'
import { parseOptimizerCSV, parsePasteText } from '../csvParser'

describe('parseOptimizerCSV', () => {
  it('parses valid CSV with required columns', () => {
    const csv = [
      'product_title,brand,keywords',
      'Widget Pro,Acme,seo|marketing|tool',
    ].join('\n')

    const result = parseOptimizerCSV(csv)
    expect(result).toHaveLength(1)
    expect(result[0].product_title).toBe('Widget Pro')
    expect(result[0].brand).toBe('Acme')
    expect(result[0].keywords).toEqual(['seo', 'marketing', 'tool'])
  })

  it('includes optional columns when present', () => {
    const csv = [
      'product_title,brand,keywords,asin,category,product_line',
      'Gadget,BrandX,kw1|kw2,B001ABC,Electronics,Pro Line',
    ].join('\n')

    const result = parseOptimizerCSV(csv)
    expect(result[0].asin).toBe('B001ABC')
    expect(result[0].category).toBe('Electronics')
    expect(result[0].product_line).toBe('Pro Line')
  })

  it('skips rows missing required fields', () => {
    const csv = [
      'product_title,brand,keywords',
      'Good,Brand,kw1',
      ',Brand,kw2',
      'Good2,,kw3',
      'Good3,Brand3,',
    ].join('\n')

    const result = parseOptimizerCSV(csv)
    expect(result).toHaveLength(1)
    expect(result[0].product_title).toBe('Good')
  })

  it('trims whitespace from headers and values', () => {
    const csv = [
      ' Product Title , Brand , Keywords ',
      ' Trimmed , CleanBrand , a|b ',
    ].join('\n')

    const result = parseOptimizerCSV(csv)
    expect(result).toHaveLength(1)
    expect(result[0].product_title).toBe('Trimmed')
    expect(result[0].brand).toBe('CleanBrand')
  })

  it('handles empty input', () => {
    expect(parseOptimizerCSV('')).toEqual([])
  })

  it('filters empty keywords from pipe-separated list', () => {
    const csv = [
      'product_title,brand,keywords',
      'Test,B,||valid||',
    ].join('\n')

    const result = parseOptimizerCSV(csv)
    expect(result[0].keywords).toEqual(['valid'])
  })
})

describe('parsePasteText', () => {
  it('parses pipe-separated lines', () => {
    const text = 'Widget Pro|Acme|seo,marketing,tool'
    const result = parsePasteText(text)

    expect(result).toHaveLength(1)
    expect(result[0].product_title).toBe('Widget Pro')
    expect(result[0].brand).toBe('Acme')
    expect(result[0].keywords).toEqual(['seo', 'marketing', 'tool'])
  })

  it('handles multiple lines', () => {
    const text = [
      'Product A|Brand A|kw1,kw2',
      'Product B|Brand B|kw3,kw4',
    ].join('\n')

    const result = parsePasteText(text)
    expect(result).toHaveLength(2)
  })

  it('skips lines with fewer than 3 parts', () => {
    const text = [
      'Good|Brand|kw1',
      'Bad|Only',
      'Short',
    ].join('\n')

    const result = parsePasteText(text)
    expect(result).toHaveLength(1)
  })

  it('skips lines where keywords are empty after filtering', () => {
    const text = 'Title|Brand|,,'
    const result = parsePasteText(text)
    expect(result).toHaveLength(0)
  })

  it('skips empty lines', () => {
    const text = '\n\nProduct|Brand|kw\n\n'
    const result = parsePasteText(text)
    expect(result).toHaveLength(1)
  })
})
