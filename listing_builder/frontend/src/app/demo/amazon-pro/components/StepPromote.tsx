// frontend/src/app/demo/amazon-pro/components/StepPromote.tsx
// Purpose: Step 5 — Coupon creation form + dry-run result
// NOT for: Real coupon management (that's sp_api_promotions.py)

'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import { Tag, CheckCircle, Lock } from 'lucide-react'

interface StepPromoteProps {
  product: any
  onComplete: (couponResult: any) => void
}

const inputCls = 'w-full rounded-lg border border-gray-700 bg-[#121212] px-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-white/20'

export default function StepPromote({ product, onComplete }: StepPromoteProps) {
  const [discount, setDiscount] = useState(15)
  const [budget, setBudget] = useState(100)
  const [days, setDays] = useState(14)

  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post('/demo/create-coupon', {
        seller_id: '',
        asins: [product.asin],
        discount_type: 'PERCENTAGE',
        discount_value: discount,
        budget,
        duration_days: days,
        name: `Promo ${product.brand} -${discount}%`,
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
        <h2 className="text-lg font-semibold text-white mb-1">Kupon promocyjny</h2>
        <p className="text-sm text-gray-400">Utwórz kupon rabatowy przez Amazon Coupons API</p>
      </div>

      {!result && (
        <>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Rabat (%)</label>
              <input
                type="number"
                value={discount}
                onChange={(e) => setDiscount(Math.max(1, Math.min(80, Number(e.target.value))))}
                className={inputCls}
                min={1}
                max={80}
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Budżet (EUR)</label>
              <input
                type="number"
                value={budget}
                onChange={(e) => setBudget(Math.max(10, Number(e.target.value)))}
                className={inputCls}
                min={10}
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Czas trwania (dni)</label>
              <input
                type="number"
                value={days}
                onChange={(e) => setDays(Math.max(1, Math.min(90, Number(e.target.value))))}
                className={inputCls}
                min={1}
                max={90}
              />
            </div>
          </div>

          <div className="text-xs text-gray-500 bg-[#121212] rounded-lg p-3 space-y-1">
            <p>ASIN: <span className="text-white">{product.asin}</span></p>
            <p>Szacowane użycia: <span className="text-white">~{Math.round(budget / (discount * 0.2))}</span></p>
            <p>Koszt na użycie: <span className="text-white">~{(discount * 0.2).toFixed(2)} EUR</span></p>
          </div>

          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-40 flex items-center justify-center gap-2"
          >
            <Tag className="w-4 h-4" />
            {mutation.isPending ? 'Tworzenie...' : 'Utwórz kupon (Dry Run)'}
          </button>
        </>
      )}

      {result && (
        <div className="border border-green-900/50 rounded-xl p-4 bg-green-950/20 space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <span className="text-sm font-medium text-green-400">
              {result.status === 'DRY_RUN' ? 'Symulacja kuponu' : 'Kupon utworzony'}
            </span>
          </div>

          {result.coupon && (
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <p className="text-gray-500">Nazwa</p>
                <p className="text-white">{result.coupon.name}</p>
              </div>
              <div>
                <p className="text-gray-500">Rabat</p>
                <p className="text-white">{result.coupon.discount_value}% ({result.coupon.discount_type})</p>
              </div>
              <div>
                <p className="text-gray-500">Budżet</p>
                <p className="text-white">{result.coupon.budget} {result.coupon.currency}</p>
              </div>
              <div>
                <p className="text-gray-500">Szac. użycia</p>
                <p className="text-white">~{result.coupon.estimated_redemptions}</p>
              </div>
              <div>
                <p className="text-gray-500">Start</p>
                <p className="text-white">{new Date(result.coupon.start_date).toLocaleDateString('pl-PL')}</p>
              </div>
              <div>
                <p className="text-gray-500">Koniec</p>
                <p className="text-white">{new Date(result.coupon.end_date).toLocaleDateString('pl-PL')}</p>
              </div>
            </div>
          )}

          {result.status === 'DRY_RUN' && (
            <div className="flex items-center gap-2 text-xs text-gray-500 border-t border-gray-800 pt-2">
              <Lock className="w-3 h-3" />
              <span>Podłącz konto Amazon SP-API aby utworzyć kupon naprawdę</span>
            </div>
          )}

          <div className="border-t border-gray-800 pt-3 text-center">
            <p className="text-sm text-green-400 font-medium">Demo zakończone!</p>
            <p className="text-xs text-gray-500 mt-1">Cały pipeline: ASIN → AI Optymalizacja → Compliance → Publikacja → Promocja</p>
          </div>
        </div>
      )}
    </div>
  )
}
