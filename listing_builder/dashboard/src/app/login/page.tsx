// src/app/login/page.tsx
// Purpose: Mock login page for demo — accepts email/password and redirects to dashboard
// NOT for: Real authentication (no backend auth, no session management)

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, Loader2 } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');

    // Basic validation — just check fields aren't empty
    if (!email.trim() || !password.trim()) {
      setError('Please enter both email and password.');
      return;
    }

    // Mock auth delay, then redirect to dashboard
    setLoading(true);
    setTimeout(() => {
      router.push('/dashboard');
    }, 800);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#121212] px-4">
      <div className="w-full max-w-sm">
        {/* Logo + branding */}
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-500/20">
            <Shield className="h-7 w-7 text-green-500" />
          </div>
          <h1 className="text-xl font-semibold text-white">Compliance Guard</h1>
          <p className="text-sm text-neutral-400">Sign in to your account</p>
        </div>

        {/* Login card */}
        <form
          onSubmit={handleSubmit}
          className="rounded-lg border border-border bg-card p-6 space-y-5"
        >
          {/* Error message */}
          {error && (
            <p className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-400">
              {error}
            </p>
          )}

          {/* Email */}
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@company.com"
              className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-white placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-green-500"
            />
          </div>

          {/* Password */}
          <div>
            <div className="mb-1 flex items-center justify-between">
              <label className="text-xs text-muted-foreground">Password</label>
              <button
                type="button"
                className="text-xs text-green-500 hover:text-green-400"
                onClick={() => {
                  // Placeholder — no real forgot password flow
                }}
              >
                Forgot password?
              </button>
            </div>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-white placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-green-500"
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-500 py-2.5 text-sm font-medium text-black transition-colors hover:bg-green-400 disabled:opacity-70"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Footer links */}
        <div className="mt-6 flex flex-col items-center gap-2 text-sm">
          <p className="text-neutral-400">
            No account?{' '}
            <a href="/#pricing" className="text-green-500 hover:text-green-400">
              Start Free Trial
            </a>
          </p>
          <a href="/" className="text-neutral-500 hover:text-neutral-300">
            Back to home
          </a>
        </div>
      </div>
    </div>
  );
}
