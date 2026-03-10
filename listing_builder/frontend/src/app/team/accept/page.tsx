// frontend/src/app/team/accept/page.tsx
// Purpose: Accept team invitation via token from URL
// NOT for: Team management (that's /team/page.tsx)

'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { acceptInvitation } from '@/lib/api/teams'

// WHY: Next.js 14 requires Suspense boundary for useSearchParams
export default function AcceptInvitationPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-[60vh] items-center justify-center p-6">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    }>
      <AcceptInvitationContent />
    </Suspense>
  )
}

function AcceptInvitationContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get('token') || ''
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [teamName, setTeamName] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setErrorMsg('Brak tokenu zaproszenia')
      return
    }

    acceptInvitation(token)
      .then((result) => {
        setTeamName(result.team_name)
        setStatus('success')
      })
      .catch((err) => {
        setErrorMsg(err.message || 'Nie udalo sie przyjac zaproszenia')
        setStatus('error')
      })
  }, [token])

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <Card className="max-w-md">
        <CardContent className="p-8 text-center">
          {status === 'loading' && (
            <>
              <Loader2 className="mx-auto mb-4 h-8 w-8 animate-spin text-gray-400" />
              <p className="text-gray-400">Akceptowanie zaproszenia...</p>
            </>
          )}
          {status === 'success' && (
            <>
              <CheckCircle className="mx-auto mb-4 h-8 w-8 text-green-400" />
              <p className="mb-2 text-lg font-medium text-white">Dolaczyles do zespolu</p>
              <p className="mb-6 text-sm text-gray-400">{teamName}</p>
              <Button onClick={() => router.push('/team')}>Przejdz do zespolu</Button>
            </>
          )}
          {status === 'error' && (
            <>
              <XCircle className="mx-auto mb-4 h-8 w-8 text-red-400" />
              <p className="mb-2 text-lg font-medium text-white">Blad</p>
              <p className="mb-6 text-sm text-gray-400">{errorMsg}</p>
              <Button variant="outline" onClick={() => router.push('/team')}>Przejdz do zespolu</Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
