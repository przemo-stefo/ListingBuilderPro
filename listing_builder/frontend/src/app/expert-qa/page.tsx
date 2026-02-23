// frontend/src/app/expert-qa/page.tsx
// Purpose: Expert Q&A chatbot — answers marketplace questions using RAG knowledge base
// NOT for: Listing optimization (that's /optimize)

'use client'

import { useState, useRef, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { Send, Loader2, Brain, BookOpen, Settings2, FileText, Sparkles, Database, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { FaqSection } from '@/components/ui/FaqSection'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  sourcesUsed?: number
}

// WHY: RAG behavior modes control how strictly the LLM sticks to transcript knowledge
const RAG_MODES = [
  { value: 'strict', label: 'Ścisły', desc: 'Tylko wiedza z transkrypcji' },
  { value: 'balanced', label: 'Zbalansowany', desc: 'Transkrypcje + ogólne porady' },
  { value: 'flexible', label: 'Elastyczny', desc: 'Łączy wszystkie źródła' },
  { value: 'bypass', label: 'Bez RAG', desc: 'Czysty LLM, bez transkrypcji' },
] as const

const SUGGESTED_QUESTIONS = [
  'Jak znaleźć najlepsze słowa kluczowe dla mojego listingu na Amazon?',
  'Jaka jest idealna struktura tytułu na Amazon DE?',
  'Jak działa algorytm A9/COSMO i jak rankuje listingi?',
  'Jakie są najlepsze praktyki dla backend keywords?',
  'Jak optymalizować kampanie PPC dla nowych produktów?',
  'Jak tworzyć skuteczne reklamy wideo na Amazon?',
]

// WHY: Next.js 14 requires Suspense boundary around useSearchParams()
function ExpertQAContent() {
  const searchParams = useSearchParams()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [mode, setMode] = useState('balanced')
  const [showModeSelector, setShowModeSelector] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const initialQuestionSent = useRef(false)

  // WHY: Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // WHY: Auto-send question from Dashboard widget (?q= param)
  useEffect(() => {
    const q = searchParams.get('q')
    if (q && !initialQuestionSent.current) {
      initialQuestionSent.current = true
      handleSend(q)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  async function handleSend(question?: string) {
    const q = question || input.trim()
    if (!q || isLoading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: q }])
    setIsLoading(true)

    try {
      const res = await fetch('/api/proxy/knowledge/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, mode }),
      })

      if (!res.ok) {
        throw new Error(`${res.status}`)
      }

      const data = await res.json()
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          sources: data.sources || [],
          sourcesUsed: data.sources_used || 0,
        },
      ])
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Nie udało się uzyskać odpowiedzi. Spróbuj ponownie.' },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-[calc(100vh-2rem)] flex-col space-y-4">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-green-500/20 p-2">
            <Brain className="h-6 w-6 text-green-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Ekspert AI</h1>
            <p className="text-xs text-green-400">Twój osobisty doradca e-commerce</p>
          </div>
          {/* WHY: Mode selector toggle — small gear icon keeps header clean */}
          <button
            onClick={() => setShowModeSelector(!showModeSelector)}
            className="ml-auto rounded-lg border border-gray-800 p-2 text-gray-400 transition-colors hover:border-gray-600 hover:text-white"
            title="Tryb RAG"
          >
            <Settings2 className="h-4 w-4" />
          </button>
        </div>

        {/* WHY: Stats bar — shows knowledge base size, builds credibility */}
        <div className="mt-3 flex flex-wrap gap-3">
          <div className="flex items-center gap-1.5 rounded-md bg-green-900/20 border border-green-900/30 px-2.5 py-1">
            <Database className="h-3 w-3 text-green-400" />
            <span className="text-[11px] text-green-400 font-medium">10 266 fragmentów wiedzy</span>
          </div>
          <div className="flex items-center gap-1.5 rounded-md bg-gray-800/50 border border-gray-700/50 px-2.5 py-1">
            <BookOpen className="h-3 w-3 text-gray-400" />
            <span className="text-[11px] text-gray-400">Baza wiedzy e-commerce</span>
          </div>
          <div className="flex items-center gap-1.5 rounded-md bg-gray-800/50 border border-gray-700/50 px-2.5 py-1">
            <Zap className="h-3 w-3 text-gray-400" />
            <span className="text-[11px] text-gray-400">AI — odpowiedź w sekundy</span>
          </div>
        </div>

        {/* WHY: Mode selector — collapsible to avoid clutter for casual users */}
        {showModeSelector && (
          <div className="mt-3 flex flex-wrap gap-2">
            {RAG_MODES.map(m => (
              <button
                key={m.value}
                onClick={() => setMode(m.value)}
                className={cn(
                  'rounded-lg border px-3 py-1.5 text-xs transition-colors',
                  mode === m.value
                    ? 'border-green-600 bg-green-900/30 text-green-400'
                    : 'border-gray-800 bg-[#1A1A1A] text-gray-400 hover:border-gray-600'
                )}
                title={m.desc}
              >
                {m.label}
                <span className="ml-1.5 text-[10px] text-gray-500">{m.desc}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto rounded-lg border border-gray-800 bg-[#121212] p-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center space-y-8">
            {/* WHY: Hero empty state — showcases Expert AI value before first question */}
            <div className="text-center space-y-3">
              <div className="mx-auto rounded-2xl bg-green-500/10 border border-green-900/30 p-4 w-fit">
                <Sparkles className="h-10 w-10 text-green-400" />
              </div>
              <h2 className="text-xl font-bold text-white">
                Wiedza ekspertów w zasięgu pytania
              </h2>
              <p className="text-sm text-gray-400 max-w-md">
                Baza wiedzy budowana latami z kursów najlepszych praktyków Amazon, PPC i e-commerce.
                Zadaj pytanie — dostaniesz konkretną odpowiedź z podaniem źródeł.
              </p>
            </div>
            <div className="grid max-w-2xl grid-cols-1 gap-2 sm:grid-cols-2">
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(q)}
                  className="rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-left text-sm text-gray-400 transition-colors hover:border-green-800 hover:text-green-300"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={cn(
                  'flex',
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={cn(
                    'max-w-[80%] rounded-lg px-4 py-3 text-sm',
                    msg.role === 'user'
                      ? 'bg-white text-black'
                      : 'border border-gray-800 bg-[#1A1A1A] text-gray-200'
                  )}
                >
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                  {/* WHY: Source attribution under assistant messages — builds trust */}
                  {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 border-t border-gray-800 pt-2">
                      <div className="flex items-center gap-1.5 text-[10px] text-green-500 font-medium mb-1">
                        <FileText className="h-3 w-3" />
                        Źródła ({msg.sourcesUsed})
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {msg.sources.map((s, j) => (
                          <span
                            key={j}
                            className="inline-block rounded bg-green-900/20 border border-green-900/30 px-1.5 py-0.5 text-[10px] text-green-400"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-gray-400">
                  <Loader2 className="h-4 w-4 animate-spin text-green-400" />
                  {mode === 'bypass' ? 'Myślę...' : 'Przeszukuję bazę wiedzy...'}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder="Zapytaj o słowa kluczowe, listingi, PPC, ranking, reklamy..."
          className="flex-1 rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white placeholder-gray-500 outline-none focus:border-green-800"
          disabled={isLoading}
        />
        <Button
          onClick={() => handleSend()}
          disabled={!input.trim() || isLoading}
          className="px-4"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* WHY: FAQ at bottom — visible when chat is empty or user scrolls down */}
      {messages.length === 0 && (
        <FaqSection
          title="FAQ — Ekspert AI"
          subtitle="Jak korzystać z bazy wiedzy eksperckiej"
          items={[
            { question: 'Co to jest Ekspert AI?', answer: 'Chatbot AI z dostępem do bazy wiedzy o sprzedaży na marketplace. Odpowiada na pytania o Amazon, eBay, Kaufland — słowa kluczowe, listingi, PPC, strategie cenowe, backend keywords i wiele więcej.' },
            { question: 'Skąd pochodzi wiedza?', answer: 'Baza wiedzy zawiera ponad 10 000 fragmentów z kursów ekspertów marketplace, poradników e-commerce i sprawdzonych strategii sprzedażowych. Wiedza jest regularnie aktualizowana.' },
            { question: 'Co oznaczają tryby RAG?', answer: 'Ścisły = odpowiedzi tylko z bazy wiedzy. Zbalansowany = baza + ogólna wiedza AI. Elastyczny = łączy wszystkie źródła. Bez RAG = czysty LLM bez bazy wiedzy. Domyślnie: Zbalansowany.' },
            { question: 'Jakie pytania mogę zadawać?', answer: 'Wszystko o sprzedaży online: jak pisać tytuły, jak dobierać słowa kluczowe, jak optymalizować PPC, jak tworzyć reklamy wideo, jak budować markę na Amazon, jakie są najlepsze praktyki dla backend keywords, itp.' },
          ]}
        />
      )}
    </div>
  )
}

export default function ExpertQAPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
      </div>
    }>
      <ExpertQAContent />
    </Suspense>
  )
}
