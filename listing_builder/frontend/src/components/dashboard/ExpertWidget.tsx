// frontend/src/components/dashboard/ExpertWidget.tsx
// Purpose: Expert AI question widget — extracted from dashboard for file size compliance
// NOT for: Full Expert QA page

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Brain, Send, ArrowRight } from 'lucide-react'

const SUGGESTED_QUESTIONS = [
  'Jak znaleźć najlepsze słowa kluczowe?',
  'Jak zoptymalizować tytuł na Amazon DE?',
  'Jak działa algorytm A9/COSMO?',
]

export function ExpertWidget() {
  const router = useRouter()
  const [question, setQuestion] = useState('')

  const handleSubmit = () => {
    if (!question.trim()) return
    router.push(`/expert-qa?q=${encodeURIComponent(question.trim())}`)
  }

  return (
    <Card className="border-green-900/30">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-green-400" />
          <CardTitle className="text-green-400">Zapytaj Eksperta AI</CardTitle>
        </div>
        <CardDescription>
          Odpowiedzi na bazie wiedzy eksperckiej o Amazon, e-commerce i PPC
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            placeholder="Np. Jak zoptymalizować backend keywords?"
            className="flex-1 rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-green-800"
          />
          <button
            onClick={handleSubmit}
            disabled={!question.trim()}
            className="rounded-lg bg-green-900/40 px-4 py-2.5 text-green-400 hover:bg-green-900/60 transition-colors disabled:opacity-40"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => router.push(`/expert-qa?q=${encodeURIComponent(q)}`)}
              className="rounded-lg border border-gray-800 bg-[#1A1A1A] px-3 py-1.5 text-xs text-gray-400 hover:border-green-800 hover:text-green-400 transition-colors"
            >
              {q}
              <ArrowRight className="inline ml-1 h-3 w-3" />
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
