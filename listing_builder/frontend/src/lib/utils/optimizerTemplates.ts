// frontend/src/lib/utils/optimizerTemplates.ts
// Purpose: Save/load optimizer form templates (localStorage)
// NOT for: API calls or UI rendering

export interface OptimizerTemplate {
  id: string
  name: string
  marketplace: string
  mode: string
  accountType: string
  brand: string
  productLine: string
  category: string
  keywordsText: string
  llmProvider: string
  createdAt: string
}

const STORAGE_KEY = 'lbp_optimizer_templates'

export function getTemplates(): OptimizerTemplate[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function saveTemplate(template: Omit<OptimizerTemplate, 'id' | 'createdAt'>): OptimizerTemplate {
  const templates = getTemplates()
  // WHY: Max 20 templates to prevent localStorage bloat
  if (templates.length >= 20) {
    templates.pop()
  }
  const newTemplate: OptimizerTemplate = {
    ...template,
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
  }
  templates.unshift(newTemplate)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(templates))
  return newTemplate
}

export function deleteTemplate(id: string): void {
  const templates = getTemplates().filter((t) => t.id !== id)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(templates))
}

export function renameTemplate(id: string, name: string): void {
  const templates = getTemplates()
  const t = templates.find((t) => t.id === id)
  if (t) {
    t.name = name
    localStorage.setItem(STORAGE_KEY, JSON.stringify(templates))
  }
}
