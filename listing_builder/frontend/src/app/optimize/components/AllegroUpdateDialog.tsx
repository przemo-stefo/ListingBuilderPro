// frontend/src/app/optimize/components/AllegroUpdateDialog.tsx
// Purpose: Modal dialog for updating an existing Allegro offer with optimized listing
// NOT for: OAuth flow or fetching offers

'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Loader2, CheckCircle, XCircle, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { updateAllegroOffer } from '@/lib/api/allegro'

// WHY regex: Allegro URLs have format allegro.pl/oferta/slug-12345678
// The offer ID is always 8-14 digits at the end of the URL
function extractOfferId(input: string): string | null {
  const trimmed = input.trim()
  // Pure numeric ID
  if (/^\d{8,14}$/.test(trimmed)) return trimmed
  // URL with offer ID
  const match = trimmed.match(/allegro\.pl\/oferta\/.*?(\d{8,})/)
  return match ? match[1] : null
}

type DialogState = 'idle' | 'loading' | 'success' | 'error'

interface AllegroUpdateDialogProps {
  open: boolean
  onClose: () => void
  title: string
  descriptionHtml: string
}

export default function AllegroUpdateDialog({
  open,
  onClose,
  title,
  descriptionHtml,
}: AllegroUpdateDialogProps) {
  const [input, setInput] = useState('')
  const [state, setState] = useState<DialogState>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  const handleClose = useCallback(() => {
    setInput('')
    setState('idle')
    setErrorMsg('')
    onClose()
  }, [onClose])

  const inputRef = useRef<HTMLInputElement>(null)

  // WHY: Users expect Escape to close modals — standard keyboard UX
  useEffect(() => {
    if (!open) return
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') handleClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [open, handleClose])

  // WHY: Prevent background scroll when modal is open
  useEffect(() => {
    if (!open) return
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [open])

  // WHY: Auto-focus input for immediate typing
  useEffect(() => {
    if (open && state === 'idle') inputRef.current?.focus()
  }, [open, state])

  if (!open) return null

  const offerId = extractOfferId(input)

  async function handleSubmit() {
    if (!offerId) return
    setState('loading')
    setErrorMsg('')
    try {
      await updateAllegroOffer(offerId, {
        title,
        description_html: descriptionHtml,
      })
      setState('success')
    } catch (err: unknown) {
      setState('error')
      setErrorMsg(err instanceof Error ? err.message : 'Nieznany blad')
    }
  }

  return (
    // WHY onClick on backdrop: standard UX — click outside modal closes it
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={handleClose}>
      <div className="w-full max-w-md rounded-xl border border-gray-800 bg-[#121212] p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Aktualizuj oferte na Allegro</h2>
          <button onClick={handleClose} className="text-gray-500 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        {state === 'success' ? (
          <div className="flex flex-col items-center gap-3 py-6">
            <CheckCircle className="h-10 w-10 text-green-400" />
            <p className="text-sm text-green-400">Oferta zaktualizowana!</p>
            <Button variant="outline" size="sm" onClick={handleClose}>Zamknij</Button>
          </div>
        ) : (
          <>
            <p className="mb-3 text-sm text-gray-400">
              Wklej link do oferty Allegro lub samo ID oferty.
            </p>
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => { setInput(e.target.value); setState('idle') }}
              placeholder="https://allegro.pl/oferta/... lub 12345678"
              disabled={state === 'loading'}
            />

            {input && !offerId && (
              <p className="mt-2 text-xs text-red-400">Nie rozpoznano ID oferty z podanego linku.</p>
            )}

            {/* WHY: Allegro title limit is 75 chars, optimizer may generate up to 200 */}
            {title.length > 75 && (
              <p className="mt-2 text-xs text-amber-400">
                Tytul ma {title.length} znakow (limit Allegro: 75). Zostanie obciety.
              </p>
            )}

            {state === 'error' && (
              <div className="mt-2 flex items-center gap-2 text-xs text-red-400">
                <XCircle className="h-3 w-3 shrink-0" />
                {errorMsg}
              </div>
            )}

            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={handleClose} disabled={state === 'loading'}>
                Anuluj
              </Button>
              <Button
                size="sm"
                onClick={handleSubmit}
                disabled={!offerId || state === 'loading'}
              >
                {state === 'loading' ? (
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                ) : null}
                Aktualizuj
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
