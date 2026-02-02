// src/components/Sidebar.tsx
// Purpose: Navigation sidebar
// NOT for: Business logic

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Bell,
  Package,
  ShoppingCart,
  BarChart3,
  Settings,
  Shield
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Alerts', href: '/dashboard/alerts', icon: Bell },
  { name: 'Inventory', href: '/dashboard/inventory', icon: Package },
  { name: 'Buy Box', href: '/dashboard/buy-box', icon: ShoppingCart },
  { name: 'Metrics', href: '/dashboard/metrics', icon: BarChart3 },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-border bg-card">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b border-border px-6">
        <Shield className="h-8 w-8 text-green-500" />
        <div>
          <h1 className="font-bold text-white">Compliance Guard</h1>
          <p className="text-xs text-muted-foreground">Monitoring Dashboard</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="mt-6 px-4">
        <ul className="space-y-1">
          {navigation.map((item) => {
            // Exact match for Dashboard, prefix match for sub-pages
            const isActive = item.href === '/dashboard'
              ? pathname === '/dashboard'
              : pathname.startsWith(item.href);
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-green-500/10 text-green-500'
                      : 'text-muted-foreground hover:bg-muted hover:text-white'
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Status indicator */}
      <div className="absolute bottom-0 left-0 right-0 border-t border-border p-4">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs text-muted-foreground">API Connected</span>
        </div>
      </div>
    </aside>
  );
}
