// src/app/dashboard/settings/page.tsx
// Purpose: Settings page for marketplace connections, notifications, and API config
// NOT for: Actual settings persistence (replace with real backend later)

'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { MarketplaceBadge } from '@/components/ui/badge';
import {
  Settings,
  Bell,
  Link2,
  Key,
  Save,
  CheckCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Mock marketplace connection state
interface MarketplaceConnection {
  marketplace: string;
  connected: boolean;
  lastSync: string | null;
}

const initialConnections: MarketplaceConnection[] = [
  { marketplace: 'amazon', connected: true, lastSync: '2 hours ago' },
  { marketplace: 'ebay', connected: true, lastSync: '3 hours ago' },
  { marketplace: 'kaufland', connected: true, lastSync: '1 hour ago' },
  { marketplace: 'allegro', connected: false, lastSync: null },
  { marketplace: 'temu', connected: false, lastSync: null },
];

// Notification preference toggles
interface NotificationPrefs {
  emailAlerts: boolean;
  criticalOnly: boolean;
  dailyDigest: boolean;
  buyBoxLost: boolean;
  lowStock: boolean;
  policyViolation: boolean;
}

export default function SettingsPage() {
  const [connections, setConnections] = useState(initialConnections);
  const [notifications, setNotifications] = useState<NotificationPrefs>({
    emailAlerts: true,
    criticalOnly: false,
    dailyDigest: true,
    buyBoxLost: true,
    lowStock: true,
    policyViolation: true,
  });
  const [apiKey, setApiKey] = useState('cg_live_••••••••••••••••');
  const [saved, setSaved] = useState(false);

  function toggleConnection(marketplace: string) {
    setConnections(prev =>
      prev.map(c =>
        c.marketplace === marketplace
          ? { ...c, connected: !c.connected, lastSync: !c.connected ? 'just now' : null }
          : c
      )
    );
  }

  function toggleNotification(key: keyof NotificationPrefs) {
    setNotifications(prev => ({ ...prev, [key]: !prev[key] }));
  }

  function handleSave() {
    // Mock save — in production this would call the API
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Settings</h1>
          <p className="text-muted-foreground">
            Manage marketplace connections, notifications, and API access
          </p>
        </div>
        <button
          onClick={handleSave}
          className={cn(
            'flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors',
            saved
              ? 'bg-green-500/20 text-green-500'
              : 'bg-green-500 text-black hover:bg-green-400'
          )}
        >
          {saved ? (
            <>
              <CheckCircle className="h-4 w-4" />
              Saved
            </>
          ) : (
            <>
              <Save className="h-4 w-4" />
              Save Changes
            </>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Marketplace Connections */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Link2 className="h-5 w-5 text-blue-500" />
              Marketplace Connections
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {connections.map(conn => (
                <div
                  key={conn.marketplace}
                  className="flex items-center justify-between rounded-lg border border-border p-3"
                >
                  <div className="flex items-center gap-3">
                    <MarketplaceBadge marketplace={conn.marketplace} />
                    <div>
                      <p className="text-sm font-medium capitalize text-white">
                        {conn.marketplace}
                      </p>
                      {conn.lastSync && (
                        <p className="text-xs text-muted-foreground">
                          Last sync: {conn.lastSync}
                        </p>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => toggleConnection(conn.marketplace)}
                    className={cn(
                      'rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
                      conn.connected
                        ? 'bg-green-500/10 text-green-500 hover:bg-green-500/20'
                        : 'bg-muted text-muted-foreground hover:bg-muted/80'
                    )}
                  >
                    {conn.connected ? 'Connected' : 'Connect'}
                  </button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Notification Preferences */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-yellow-500" />
              Notifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <ToggleRow
                label="Email Alerts"
                description="Receive alert notifications via email"
                checked={notifications.emailAlerts}
                onChange={() => toggleNotification('emailAlerts')}
              />
              <ToggleRow
                label="Critical Only"
                description="Only notify for critical severity alerts"
                checked={notifications.criticalOnly}
                onChange={() => toggleNotification('criticalOnly')}
              />
              <ToggleRow
                label="Daily Digest"
                description="Receive a daily summary of all activity"
                checked={notifications.dailyDigest}
                onChange={() => toggleNotification('dailyDigest')}
              />

              <div className="border-t border-border pt-4">
                <p className="mb-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Alert Types
                </p>
                <div className="space-y-4">
                  <ToggleRow
                    label="Buy Box Lost"
                    description="Notify when you lose the Buy Box"
                    checked={notifications.buyBoxLost}
                    onChange={() => toggleNotification('buyBoxLost')}
                  />
                  <ToggleRow
                    label="Low Stock"
                    description="Notify when inventory drops below threshold"
                    checked={notifications.lowStock}
                    onChange={() => toggleNotification('lowStock')}
                  />
                  <ToggleRow
                    label="Policy Violation"
                    description="Notify on compliance or policy issues"
                    checked={notifications.policyViolation}
                    onChange={() => toggleNotification('policyViolation')}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API Configuration */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5 text-orange-500" />
              API Configuration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">API Key</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={apiKey}
                    onChange={e => setApiKey(e.target.value)}
                    className="flex-1 rounded-lg border border-border bg-card px-3 py-2 font-mono text-sm text-white focus:outline-none focus:ring-1 focus:ring-green-500"
                    readOnly
                  />
                  <button
                    className="rounded-lg border border-border bg-card px-3 py-2 text-xs text-muted-foreground hover:bg-muted transition-colors"
                    onClick={() => {
                      // Mock regenerate
                      setApiKey('cg_live_' + Math.random().toString(36).substring(2, 18));
                    }}
                  >
                    Regenerate
                  </button>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Used to authenticate requests to the Compliance Guard API
                </p>
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Webhook URL</label>
                <input
                  type="text"
                  placeholder="https://your-domain.com/webhook"
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-white placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-green-500"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  Receive real-time alert notifications via webhook
                </p>
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Refresh Interval</label>
                <select className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-green-500">
                  <option value="5">Every 5 minutes</option>
                  <option value="15">Every 15 minutes</option>
                  <option value="30" selected>Every 30 minutes</option>
                  <option value="60">Every hour</option>
                </select>
                <p className="mt-1 text-xs text-muted-foreground">
                  How often to check marketplaces for updates
                </p>
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted-foreground">Low Stock Threshold</label>
                <input
                  type="number"
                  defaultValue={20}
                  min={1}
                  max={999}
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-green-500"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  Trigger low stock alerts below this quantity
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Toggle switch row — extracted to keep the main component clean
function ToggleRow({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-white">{label}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <button
        onClick={onChange}
        className={cn(
          'relative h-6 w-11 rounded-full transition-colors',
          checked ? 'bg-green-500' : 'bg-muted'
        )}
      >
        <span
          className={cn(
            'absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white transition-transform',
            checked && 'translate-x-5'
          )}
        />
      </button>
    </div>
  );
}
