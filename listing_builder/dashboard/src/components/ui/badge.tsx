// src/components/ui/badge.tsx
// Purpose: Badge component for labels and status
// NOT for: Business logic

import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';

const badgeVariants = cva(
  'inline-flex items-center rounded-md px-2 py-1 text-xs font-medium',
  {
    variants: {
      variant: {
        default: 'bg-muted text-muted-foreground',
        success: 'bg-green-500/10 text-green-400',
        warning: 'bg-yellow-500/10 text-yellow-400',
        danger: 'bg-red-500/10 text-red-400',
        info: 'bg-blue-500/10 text-blue-400',
        orange: 'bg-orange-500/10 text-orange-400',
        purple: 'bg-purple-500/10 text-purple-400',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

// Severity badge helper
export function SeverityBadge({ severity }: { severity: string }) {
  const variant = {
    critical: 'danger',
    high: 'orange',
    medium: 'warning',
    low: 'info',
  }[severity] as 'danger' | 'orange' | 'warning' | 'info' | undefined;

  return <Badge variant={variant}>{severity}</Badge>;
}

// Status badge helper
export function StatusBadge({ status }: { status: string }) {
  const variant = {
    active: 'danger',
    acknowledged: 'warning',
    resolved: 'success',
    dismissed: 'default',
  }[status] as 'danger' | 'warning' | 'success' | 'default' | undefined;

  return <Badge variant={variant}>{status}</Badge>;
}

// Marketplace badge helper
export function MarketplaceBadge({ marketplace }: { marketplace: string }) {
  const variant = {
    amazon: 'orange',
    ebay: 'info',
    allegro: 'orange',
    kaufland: 'danger',
    temu: 'purple',
  }[marketplace] as 'orange' | 'info' | 'danger' | 'purple' | undefined;

  const label = {
    amazon: 'AMZ',
    ebay: 'EBAY',
    allegro: 'ALG',
    kaufland: 'KFL',
    temu: 'TEMU',
  }[marketplace] || marketplace.toUpperCase();

  return <Badge variant={variant}>{label}</Badge>;
}
