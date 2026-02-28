// frontend/src/lib/hooks/useLocalStorage.ts
// Purpose: SSR-safe generic hook for persisting state in localStorage
// NOT for: Server-side storage or session data

import { useState, useEffect, useCallback } from 'react'

export function useLocalStorage<T>(key: string, defaultValue: T): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(defaultValue)

  // WHY: Read from localStorage only after mount (SSR-safe)
  useEffect(() => {
    try {
      const stored = localStorage.getItem(key)
      if (stored !== null) {
        setValue(JSON.parse(stored))
      }
    } catch {
      // Ignore parse errors — use default
    }
  }, [key])

  const setStoredValue = useCallback((newValue: T) => {
    setValue(newValue)
    try {
      localStorage.setItem(key, JSON.stringify(newValue))
    } catch {
      // Ignore quota errors
    }
  }, [key])

  return [value, setStoredValue]
}
