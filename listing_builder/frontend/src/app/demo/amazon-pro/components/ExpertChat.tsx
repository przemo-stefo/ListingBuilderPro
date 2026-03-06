// frontend/src/app/demo/amazon-pro/components/ExpertChat.tsx
// Purpose: Floating Amazon Expert AI chatbot — RAG-powered answers from Inner Circle transcripts
// NOT for: Production Q&A (that's /expert-qa page with auth + premium)

'use client'

import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import { MessageCircle, X, Send, Bot, User, Loader2, BookOpen } from 'lucide-react'
import type { ChatMessage, ChatResponse } from '../types'

// WHY: Suggested questions give Michał quick wins — show chatbot's expertise instantly
const SUGGESTED_QUESTIONS = [
  'Jak zoptymalizować tytuł na Amazon pod ranking?',
  'Jakie są najlepsze praktyki PPC na Amazon?',
  'Jak działa algorytm A9 i co wpływa na ranking?',
  'Jak znaleźć najlepsze keywordy do listingu?',
  'Jak zwiększyć konwersję na stronie produktu?',
]

export default function ExpertChat() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // WHY: Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // WHY: Focus input when chat opens
  useEffect(() => {
    if (isOpen) inputRef.current?.focus()
  }, [isOpen])

  const chatMutation = useMutation({
    mutationFn: async (question: string) => {
      const { data } = await apiClient.post<ChatResponse>('/demo/chat', {
        question,
        mode: 'balanced',
        expert: 'strict',
      })
      return data
    },
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
          sources_used: data.sources_used,
          timestamp: Date.now(),
        },
      ])
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Przepraszam, wystąpił błąd. Spróbuj ponownie.',
          timestamp: Date.now(),
        },
      ])
    },
  })

  const handleSend = (text?: string) => {
    const question = (text || input).trim()
    if (!question || chatMutation.isPending) return

    setMessages((prev) => [
      ...prev,
      { role: 'user', content: question, timestamp: Date.now() },
    ])
    setInput('')
    setShowSuggestions(false)
    chatMutation.mutate(question)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // WHY: Floating button + slide-up panel — doesn't interfere with wizard steps
  return (
    <>
      {/* Floating chat button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-blue-600 px-4 py-3 text-white shadow-lg hover:bg-blue-500 transition-all hover:scale-105"
        >
          <MessageCircle className="w-5 h-5" />
          <span className="text-sm font-medium">Amazon Expert AI</span>
        </button>
      )}

      {/* Chat panel */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-[420px] max-h-[600px] flex flex-col rounded-2xl border border-gray-700 bg-[#1A1A1A] shadow-2xl">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-600/20 flex items-center justify-center">
                <Bot className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">Amazon Expert AI</p>
                <p className="text-[10px] text-gray-500">Ekspert Amazon FBA</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-500 hover:text-white p-1 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-[300px] max-h-[420px]">
            {/* Welcome message */}
            {messages.length === 0 && (
              <div className="space-y-3">
                <div className="flex gap-2">
                  <div className="w-7 h-7 rounded-full bg-blue-600/20 flex-shrink-0 flex items-center justify-center mt-0.5">
                    <Bot className="w-3.5 h-3.5 text-blue-400" />
                  </div>
                  <div className="bg-gray-800/50 rounded-xl rounded-tl-sm px-3 py-2 text-sm text-gray-300">
                    <p>Cześć! Jestem ekspertem Amazon AI. Specjalizuję się w keywords, ranking, PPC i listing optimization.</p>
                    <p className="mt-1.5 text-gray-400 text-xs">Zapytaj mnie o cokolwiek związanego z Amazon FBA.</p>
                  </div>
                </div>

                {/* Suggested questions */}
                {showSuggestions && (
                  <div className="pl-9 space-y-1.5">
                    <p className="text-[10px] text-gray-600 uppercase tracking-wide">Popularne pytania</p>
                    {SUGGESTED_QUESTIONS.map((q, i) => (
                      <button
                        key={i}
                        onClick={() => handleSend(q)}
                        className="block w-full text-left text-xs text-gray-400 hover:text-white bg-gray-800/30 hover:bg-gray-800/60 rounded-lg px-3 py-2 transition-colors"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Chat messages */}
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center mt-0.5 ${
                  msg.role === 'user' ? 'bg-gray-700' : 'bg-blue-600/20'
                }`}>
                  {msg.role === 'user'
                    ? <User className="w-3.5 h-3.5 text-gray-300" />
                    : <Bot className="w-3.5 h-3.5 text-blue-400" />
                  }
                </div>
                <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-600/20 text-white rounded-tr-sm'
                    : 'bg-gray-800/50 text-gray-300 rounded-tl-sm'
                }`}>
                  {/* WHY: Render markdown-like content with line breaks */}
                  <div className="whitespace-pre-wrap break-words leading-relaxed">
                    {msg.content}
                  </div>
                  {/* Source attribution */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-700/50">
                      <div className="flex items-center gap-1 text-[10px] text-gray-500">
                        <BookOpen className="w-3 h-3" />
                        <span>Na podstawie {msg.sources_used} źródeł eksperckich</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Loading indicator */}
            {chatMutation.isPending && (
              <div className="flex gap-2">
                <div className="w-7 h-7 rounded-full bg-blue-600/20 flex-shrink-0 flex items-center justify-center mt-0.5">
                  <Bot className="w-3.5 h-3.5 text-blue-400" />
                </div>
                <div className="bg-gray-800/50 rounded-xl rounded-tl-sm px-3 py-2">
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Szukam w bazie wiedzy...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="border-t border-gray-800 px-3 py-3">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Zapytaj o Amazon..."
                disabled={chatMutation.isPending}
                className="flex-1 rounded-lg border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/30 disabled:opacity-50"
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || chatMutation.isPending}
                className="rounded-lg bg-blue-600 p-2 text-white hover:bg-blue-500 disabled:opacity-30 disabled:hover:bg-blue-600 transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <p className="text-[10px] text-gray-600 mt-1.5 text-center">
              AI ekspert Amazon FBA — wiedza o keywords, PPC, ranking, listing optimization.
            </p>
          </div>
        </div>
      )}
    </>
  )
}
