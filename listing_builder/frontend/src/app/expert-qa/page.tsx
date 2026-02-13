// frontend/src/app/expert-qa/page.tsx
// Purpose: Expert Q&A chatbot — answers marketplace questions using RAG knowledge base
// NOT for: Listing optimization (that's /optimize)

'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Brain, BookOpen, Settings2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: number
  sourceNames?: string[]
  mode?: string
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

export default function ExpertQAPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [mode, setMode] = useState('balanced')
  const [showModeSelector, setShowModeSelector] = useState(false)
  const [stats, setStats] = useState<{ total_chunks: number; total_files: number } | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // WHY: Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // WHY: Fetch knowledge base stats on mount to show in header
  useEffect(() => {
    fetch('/api/proxy/knowledge/stats')
      .then(r => r.json())
      .then(setStats)
      .catch(() => {})
  }, [])

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
          sources: data.sources_used,
          sourceNames: data.source_names || [],
          mode: data.mode,
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
          <Brain className="h-6 w-6 text-green-400" />
          <h1 className="text-2xl font-bold text-white">Ekspert Q&A</h1>
          {/* WHY: Mode selector toggle — small gear icon keeps header clean */}
          <button
            onClick={() => setShowModeSelector(!showModeSelector)}
            className="ml-auto rounded-lg border border-gray-800 p-2 text-gray-400 transition-colors hover:border-gray-600 hover:text-white"
            title="Tryb RAG"
          >
            <Settings2 className="h-4 w-4" />
          </button>
        </div>
        <p className="mt-1 text-sm text-gray-400">
          Zadaj pytanie o Amazon, e-commerce, reklamy — odpowiedzi na bazie wiedzy eksperckiej
          {stats && (
            <span className="ml-2 text-gray-500">
              ({stats.total_chunks.toLocaleString()} fragmentów z {stats.total_files} transkrypcji)
            </span>
          )}
        </p>

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
          <div className="flex h-full flex-col items-center justify-center space-y-6">
            <div className="text-center">
              <BookOpen className="mx-auto h-12 w-12 text-gray-600" />
              <h2 className="mt-3 text-lg font-medium text-gray-400">
                Zapytaj o cokolwiek
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                Słowa kluczowe, listingi, PPC, ranking, reklamy wideo, strategie kreatywne
              </p>
            </div>
            <div className="grid max-w-2xl grid-cols-1 gap-2 sm:grid-cols-2">
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(q)}
                  className="rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-left text-sm text-gray-400 transition-colors hover:border-gray-600 hover:text-white"
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
                  {msg.role === 'assistant' && (
                    <div className="mt-2 text-[10px] text-gray-500">
                      {msg.sources !== undefined && msg.sources > 0 && (
                        <>
                          <p>Na podstawie {msg.sources} {msg.sources === 1 ? 'źródła' : 'źródeł'}:</p>
                          {msg.sourceNames && msg.sourceNames.length > 0 && (
                            <div className="mt-1 flex flex-wrap gap-1">
                              {msg.sourceNames.map((name, j) => (
                                <span
                                  key={j}
                                  className="rounded bg-gray-800 px-1.5 py-0.5 text-gray-400"
                                >
                                  {name}
                                </span>
                              ))}
                            </div>
                          )}
                        </>
                      )}
                      {msg.mode && (
                        <span className="mt-1 inline-block rounded bg-gray-800/50 px-1.5 py-0.5 text-gray-500">
                          tryb: {msg.mode}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-gray-400">
                  <Loader2 className="h-4 w-4 animate-spin" />
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
          className="flex-1 rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-white placeholder-gray-500 outline-none focus:border-gray-600"
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
    </div>
  )
}
