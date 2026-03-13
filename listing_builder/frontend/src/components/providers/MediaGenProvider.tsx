// frontend/src/components/providers/MediaGenProvider.tsx
// Purpose: Global context for background media generation — polling + notifications
// NOT for: UI components or generation logic

'use client'

import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { getGenerationStatus, getActiveJobs } from '@/lib/api/mediaGeneration'
import { useToast } from '@/lib/hooks/useToast'

interface ActiveJob {
  id: number
  status: string
  media_type: string
}

interface MediaGenContextType {
  activeJobs: ActiveJob[]
  addJob: (id: number, media_type: string) => void
  completedJobIds: number[]
  clearCompleted: (id: number) => void
}

const MediaGenContext = createContext<MediaGenContextType>({
  activeJobs: [],
  addJob: () => {},
  completedJobIds: [],
  clearCompleted: () => {},
})

export function useMediaGen() {
  return useContext(MediaGenContext)
}

export function MediaGenProvider({ children }: { children: React.ReactNode }) {
  const [activeJobs, setActiveJobs] = useState<ActiveJob[]>([])
  const [completedJobIds, setCompletedJobIds] = useState<number[]>([])
  const { toast } = useToast()
  const queryClient = useQueryClient()
  // WHY: Ref tracks current jobs for the interval callback — avoids re-creating interval on every state change
  const jobsRef = useRef<ActiveJob[]>([])
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const isPollingRef = useRef(false) // WHY: Prevents concurrent polls if API is slow
  const toastRef = useRef(toast)
  toastRef.current = toast
  jobsRef.current = activeJobs

  const addJob = useCallback((id: number, media_type: string) => {
    setActiveJobs(prev => [...prev, { id, status: 'pending', media_type }])
  }, [])

  const clearCompleted = useCallback((id: number) => {
    setCompletedJobIds(prev => prev.filter(j => j !== id))
  }, [])

  // WHY: On mount, recover any in-progress jobs (handles page refresh)
  useEffect(() => {
    getActiveJobs()
      .then(data => {
        if (data.jobs.length > 0) {
          setActiveJobs(data.jobs)
        }
      })
      .catch(() => {})
  }, [])

  // WHY: Start/stop polling based on whether there are active jobs
  useEffect(() => {
    if (activeJobs.length === 0) {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
      return
    }

    if (pollingRef.current) return // WHY: Already polling — don't create duplicate intervals

    const poll = async () => {
      if (isPollingRef.current) return // WHY: Previous poll still running — skip this tick
      const currentJobs = jobsRef.current
      if (currentJobs.length === 0) return

      isPollingRef.current = true
      const updated: ActiveJob[] = []
      for (const job of currentJobs) {
        try {
          const status = await getGenerationStatus(job.id)
          if (status.status === 'completed') {
            setCompletedJobIds(prev => [...prev, job.id])
            const label = job.media_type === 'video' ? 'Wideo' : 'Grafiki A+'
            toastRef.current({ title: `${label} gotowe!`, description: 'Sprawdz w historii generacji.' })
            // WHY: Refresh Historia tab so status updates from "Generuje..." to "Gotowe"
            queryClient.invalidateQueries({ queryKey: ['media-history'] })
          } else if (status.status === 'failed') {
            toastRef.current({
              title: 'Generacja nie powiodla sie',
              description: status.error_message || 'Nieznany blad',
              variant: 'destructive',
            })
            queryClient.invalidateQueries({ queryKey: ['media-history'] })
          } else {
            updated.push({ ...job, status: status.status })
          }
        } catch {
          updated.push(job)
        }
      }
      setActiveJobs(updated)
      isPollingRef.current = false
    }

    pollingRef.current = setInterval(poll, 5000)
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [activeJobs.length]) // WHY: Only re-run when count changes (0→N or N→0), not on every poll update

  return (
    <MediaGenContext.Provider value={{ activeJobs, addJob, completedJobIds, clearCompleted }}>
      {children}
    </MediaGenContext.Provider>
  )
}
