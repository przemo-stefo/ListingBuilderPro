// frontend/src/app/monitoring/components/AlertSettingRow.tsx
// Purpose: Single row in the alert settings table (extracted for <200 line files)
// NOT for: Category headers, save logic, or data fetching

import { cn } from '@/lib/utils'
import type { AlertSettingResponse, AlertTypeSettingPayload } from '@/lib/api/alertSettings'

const PRIORITY_OPTIONS = ['minor', 'major', 'critical'] as const
const PRIORITY_COLORS: Record<string, string> = {
  minor: 'text-gray-400 bg-gray-800',
  major: 'text-yellow-400 bg-yellow-900/30',
  critical: 'text-red-400 bg-red-900/30',
}

interface Props {
  item: AlertSettingResponse
  onUpdate: (alertType: string, field: keyof AlertTypeSettingPayload, value: unknown) => void
}

export default function AlertSettingRow({ item, onUpdate }: Props) {
  return (
    <tr
      className={cn(
        'border-b border-gray-800/50 transition-colors hover:bg-white/[0.02]',
        !item.enabled && 'opacity-50'
      )}
    >
      {/* Label + badge */}
      <td className="px-4 py-2.5">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={item.enabled}
            onChange={() => onUpdate(item.alert_type, 'enabled', !item.enabled)}
            className="h-3.5 w-3.5 rounded border-gray-600 bg-gray-800 accent-blue-500"
          />
          <span className="text-gray-200">{item.label}</span>
          {!item.active && (
            <span className="rounded bg-gray-800 px-1.5 py-0.5 text-[10px] text-gray-500 uppercase">
              SP-API
            </span>
          )}
        </div>
      </td>

      {/* Priority dropdown */}
      <td className="px-4 py-2.5">
        <select
          value={item.priority}
          onChange={e => onUpdate(item.alert_type, 'priority', e.target.value)}
          className={cn(
            'rounded px-2 py-1 text-xs font-medium border-0 cursor-pointer',
            PRIORITY_COLORS[item.priority] || PRIORITY_COLORS.minor
          )}
        >
          {PRIORITY_OPTIONS.map(p => (
            <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
          ))}
        </select>
      </td>

      {/* In-App toggle */}
      <td className="px-4 py-2.5 text-center">
        <input
          type="checkbox"
          checked={item.notify_in_app}
          onChange={() => onUpdate(item.alert_type, 'notify_in_app', !item.notify_in_app)}
          className="h-3.5 w-3.5 rounded border-gray-600 bg-gray-800 accent-blue-500"
        />
      </td>

      {/* Email toggle — disabled until Faza 2 */}
      <td className="px-4 py-2.5 text-center">
        <input
          type="checkbox"
          checked={item.notify_email}
          disabled
          title="Email delivery coming soon"
          className="h-3.5 w-3.5 rounded border-gray-600 bg-gray-800 opacity-40"
        />
      </td>

      {/* Recipients — disabled until Faza 2 */}
      <td className="px-4 py-2.5">
        <input
          type="text"
          value={item.email_recipients.join(', ')}
          disabled
          placeholder="Coming soon"
          className="w-full rounded bg-gray-800/50 px-2 py-1 text-xs text-gray-500 border border-gray-700/50 opacity-40"
        />
      </td>
    </tr>
  )
}
