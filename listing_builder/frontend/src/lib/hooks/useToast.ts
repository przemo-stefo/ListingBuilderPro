// frontend/src/lib/hooks/useToast.ts
// Purpose: Toast notification hook for user feedback
// NOT for: Complex state management or business logic

import * as React from 'react'

// Toast types
type ToastProps = {
  title?: string
  description?: string
  variant?: 'default' | 'destructive'
  duration?: number
}

type Toast = ToastProps & {
  id: string
}

// Simple toast state management
const toastState = {
  toasts: [] as Toast[],
  listeners: new Set<(toasts: Toast[]) => void>(),
}

function addToast(toast: ToastProps) {
  const id = Math.random().toString(36).substr(2, 9)
  const newToast: Toast = { ...toast, id }
  toastState.toasts.push(newToast)
  toastState.listeners.forEach(listener => listener([...toastState.toasts]))

  // Auto-remove after duration (default 5s)
  setTimeout(() => {
    removeToast(id)
  }, toast.duration || 5000)

  return id
}

function removeToast(id: string) {
  toastState.toasts = toastState.toasts.filter(t => t.id !== id)
  toastState.listeners.forEach(listener => listener([...toastState.toasts]))
}

export function useToast() {
  const [toasts, setToasts] = React.useState<Toast[]>(toastState.toasts)

  React.useEffect(() => {
    toastState.listeners.add(setToasts)
    return () => {
      toastState.listeners.delete(setToasts)
    }
  }, [])

  return {
    toasts,
    toast: addToast,
    dismiss: removeToast,
  }
}
