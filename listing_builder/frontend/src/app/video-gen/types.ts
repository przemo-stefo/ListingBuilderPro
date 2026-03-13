// frontend/src/app/video-gen/types.ts
// Purpose: Shared types for video-gen page and components
// NOT for: Backend types or global app types

export type GenerationStatus = 'idle' | 'uploading' | 'generating' | 'completed' | 'error'
export type InputMode = 'file' | 'url'
export type MediaMode = 'video' | 'images'

export interface ImageResult {
  images: Record<string, string>
  image_types: string[]
  llm_provider: string
}
