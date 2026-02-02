// frontend/src/components/ui/badge.tsx
// Purpose: Badge component for status indicators
// NOT for: Interactive elements or buttons

import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-white text-black',
        secondary: 'border-transparent bg-gray-800 text-white',
        destructive: 'border-transparent bg-red-500 text-white',
        outline: 'text-white',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

// Compliance status badge with color mapping
// WHY: Centralizes compliance status → color mapping so it's consistent everywhere
function ComplianceBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    compliant: {
      label: 'Compliant',
      className: 'bg-green-500/10 text-green-500 border-green-500/20',
    },
    warning: {
      label: 'Warning',
      className: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    },
    suppressed: {
      label: 'Suppressed',
      className: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
    },
    blocked: {
      label: 'Blocked',
      className: 'bg-red-500/10 text-red-500 border-red-500/20',
    },
  }

  const c = config[status] || config.compliant

  return (
    <Badge className={cn('text-xs', c.className)}>
      {c.label}
    </Badge>
  )
}

export { Badge, badgeVariants, ComplianceBadge }
