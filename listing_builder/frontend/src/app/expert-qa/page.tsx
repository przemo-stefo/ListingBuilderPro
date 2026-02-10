// frontend/src/app/expert-qa/page.tsx
// Purpose: Expert Q&A chatbot — answers Amazon questions using Inner Circle transcript RAG
// NOT for: Listing optimization (that's /optimize)

'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Brain, BookOpen } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: number
}

const SUGGESTED_QUESTIONS = [
  'How do I find the best keywords for my Amazon listing?',
  'What is the ideal title structure for Amazon DE?',
  'How does Amazon A9 algorithm rank listings?',
  'What are the best practices for backend keywords?',
  'How to optimize PPC campaigns for new products?',
  'What coverage percentage should I target for aggressive mode?',
]

export default function ExpertQAPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
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
        body: JSON.stringify({ question: q }),
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
        },
      ])
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Failed to get answer. Please try again.' },
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
          <h1 className="text-2xl font-bold text-white">Expert Q&A</h1>
        </div>
        <p className="mt-1 text-sm text-gray-400">
          Ask Amazon questions — answered using Inner Circle transcript knowledge
          {stats && (
            <span className="ml-2 text-gray-500">
              ({stats.total_chunks.toLocaleString()} chunks from {stats.total_files} transcripts)
            </span>
          )}
        </p>
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto rounded-lg border border-gray-800 bg-[#121212] p-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center space-y-6">
            <div className="text-center">
              <BookOpen className="mx-auto h-12 w-12 text-gray-600" />
              <h2 className="mt-3 text-lg font-medium text-gray-400">
                Ask me anything about Amazon
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                Keywords, listings, PPC, ranking, optimization strategies
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
                  {msg.sources !== undefined && msg.sources > 0 && (
                    <p className="mt-2 text-[10px] text-gray-500">
                      Based on {msg.sources} transcript excerpt{msg.sources !== 1 ? 's' : ''}
                    </p>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 rounded-lg border border-gray-800 bg-[#1A1A1A] px-4 py-3 text-sm text-gray-400">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Searching transcripts...
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
          placeholder="Ask about keywords, listings, PPC, ranking..."
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
