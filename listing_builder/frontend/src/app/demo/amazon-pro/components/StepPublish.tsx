// frontend/src/app/demo/amazon-pro/components/StepPublish.tsx
// Purpose: Step 4 — Dry-run publish to Amazon with confirmation
// NOT for: Real SP-API listing creation (that's sp_api_listings.py)

'use client'

import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import { Upload, CheckCircle, Lock } from 'lucide-react'

interface StepPublishProps {
  product: any
  optimized: any
  onComplete: (publishResult: any) => void
}

export default function StepPublish({ product, optimized, onComplete }: StepPublishProps) {
  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post('/demo/publish', {
        seller_id: '',
        sku: `DEMO-${product.asin}`,
        product_type: 'DIETARY_SUPPLEMENT',
        attributes: {
          title: optimized?.title || product.title,
          bullet_points: optimized?.bullet_points || product.bullets,
          description: optimized?.description || product.description,
        },
        marketplace: product.marketplace || 'DE',
        dry_run: true,
      })
      return data
    },
    onSuccess: (data) => {
      onComplete(data)
    },
  })

  const result = mutation.data

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Opublikuj na Amazon</h2>
        <p className="text-sm text-gray-400">Dry-run mode — symulacja bez rzeczywistego push na Amazon</p>
      </div>

      {!result && (
        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-40 flex items-center justify-center gap-2"
        >
          <Upload className="w-4 h-4" />
          {mutation.isPending ? 'Symulacja...' : 'Opublikuj (Dry Run)'}
        </button>
      )}

      {result && (
        <>
          <div className="border border-green-900/50 rounded-xl p-4 bg-green-950/20 space-y-3">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <span className="text-sm font-medium text-green-400">
                {result.status === 'DRY_RUN' ? 'Symulacja zakończona' : 'Opublikowano'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <p className="text-gray-500">SKU</p>
                <p className="text-white font-mono">{result.sku}</p>
              </div>
              <div>
                <p className="text-gray-500">Marketplace</p>
                <p className="text-white">Amazon {result.marketplace}</p>
              </div>
              <div>
                <p className="text-gray-500">Atrybuty</p>
                <p className="text-white">{result.attributes_count} pól</p>
              </div>
              <div>
                <p className="text-gray-500">API Call</p>
                <p className="text-white font-mono text-[10px]">{result.would_call}</p>
              </div>
            </div>

            {result.status === 'DRY_RUN' && (
              <div className="flex items-center gap-2 text-xs text-gray-500 border-t border-gray-800 pt-2">
                <Lock className="w-3 h-3" />
                <span>Podłącz konto Amazon SP-API aby opublikować naprawdę</span>
              </div>
            )}
          </div>

          <button
            onClick={() => onComplete(result)}
            className="w-full px-4 py-2 bg-white text-black rounded-lg text-sm font-semibold hover:bg-gray-200"
          >
            Dalej — Utwórz kupon promocyjny
          </button>
        </>
      )}
    </div>
  )
}
