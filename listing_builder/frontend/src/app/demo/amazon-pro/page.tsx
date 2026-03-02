// frontend/src/app/demo/amazon-pro/page.tsx
// Purpose: Amazon Pro Demo — 5-step wizard from ASIN to coupon
// NOT for: Production listing management (that's /products and /optimize)

'use client'

import { useState } from 'react'
import { ArrowLeft, Rocket } from 'lucide-react'
import { useRouter } from 'next/navigation'
import DemoStepper from './components/DemoStepper'
import StepFetch from './components/StepFetch'
import StepOptimize from './components/StepOptimize'
import StepCompliance from './components/StepCompliance'
import StepPublish from './components/StepPublish'
import StepPromote from './components/StepPromote'
import type { DemoProduct, OptimizedListing, CoverageResult, ComplianceResult, PublishResult, CouponResult } from './types'

export default function AmazonProDemoPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)
  const [completedSteps, setCompletedSteps] = useState<number[]>([])

  // WHY separate state per step: each step's data feeds into the next
  const [product, setProduct] = useState<DemoProduct | null>(null)
  const [optimized, setOptimized] = useState<OptimizedListing | null>(null)
  const [coverage, setCoverage] = useState<CoverageResult | null>(null)
  const [complianceResult, setComplianceResult] = useState<ComplianceResult | null>(null)
  const [publishResult, setPublishResult] = useState<PublishResult | null>(null)
  const [couponResult, setCouponResult] = useState<CouponResult | null>(null)

  const completeStep = (step: number) => {
    setCompletedSteps((prev) => [...new Set([...prev, step])])
    if (step < 5) setCurrentStep(step + 1)
  }

  const handleReset = () => {
    setCurrentStep(1)
    setCompletedSteps([])
    setProduct(null)
    setOptimized(null)
    setCoverage(null)
    setComplianceResult(null)
    setPublishResult(null)
    setCouponResult(null)
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.push('/dashboard')}
          className="p-2 rounded-lg hover:bg-white/10 text-gray-400"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <Rocket className="w-5 h-5 text-blue-400" />
            <h1 className="text-xl font-bold text-white">Amazon Pro Demo</h1>
          </div>
          <p className="text-sm text-gray-500 mt-0.5">
            Pełny pipeline: ASIN → AI Optymalizacja → Compliance → Publish → Coupon
          </p>
        </div>
        {completedSteps.length > 0 && (
          <button
            onClick={handleReset}
            className="ml-auto text-xs text-gray-500 hover:text-white px-3 py-1 rounded border border-gray-800 hover:border-gray-600"
          >
            Reset demo
          </button>
        )}
      </div>

      {/* Stepper */}
      <div className="border border-gray-800 rounded-xl p-4 bg-[#1A1A1A]">
        <DemoStepper currentStep={currentStep} completedSteps={completedSteps} />
      </div>

      {/* Step Content */}
      <div className="border border-gray-800 rounded-xl p-6 bg-[#1A1A1A] min-h-[300px]">
        {currentStep === 1 && (
          <StepFetch
            onComplete={(p) => {
              setProduct(p)
              completeStep(1)
            }}
          />
        )}

        {currentStep === 2 && product && (
          <StepOptimize
            product={product}
            onComplete={(opt, cov) => {
              setOptimized(opt)
              setCoverage(cov)
              completeStep(2)
            }}
          />
        )}

        {currentStep === 3 && product && (
          <StepCompliance
            optimized={optimized}
            product={product}
            onComplete={(result) => {
              setComplianceResult(result)
              completeStep(3)
            }}
          />
        )}

        {currentStep === 4 && product && (
          <StepPublish
            product={product}
            optimized={optimized}
            onComplete={(result) => {
              setPublishResult(result)
              completeStep(4)
            }}
          />
        )}

        {currentStep === 5 && product && (
          <StepPromote
            product={product}
            onComplete={(result) => {
              setCouponResult(result)
              completeStep(5)
            }}
          />
        )}
      </div>
    </div>
  )
}
