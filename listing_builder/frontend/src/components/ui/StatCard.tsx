// frontend/src/components/ui/StatCard.tsx
// Purpose: Reusable stat card with icon, label, value, and subtitle
// NOT for: Business logic — pure presentational component

import { Card, CardContent } from '@/components/ui/card'

interface StatCardProps {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  sub: string
}

export function StatCard({ icon: Icon, label, value, sub }: StatCardProps) {
  return (
    <Card>
      <CardContent className="py-4">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-white/5 p-2">
            <Icon className="h-5 w-5 text-gray-400" />
          </div>
          <div>
            <p className="text-xs text-gray-500">{label}</p>
            <p className="text-xl font-bold text-white">{value}</p>
            <p className="text-[11px] text-gray-500">{sub}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
