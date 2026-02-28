// frontend/src/lib/utils/redirect.ts
// Purpose: Validate external redirect URLs before navigation
// NOT for: Internal Next.js routing

const ALLOWED_REDIRECT_HOSTS = [
  'checkout.stripe.com',
  'billing.stripe.com',
  'allegro.pl',
  'allegro.pl.allegrosandbox.pl',
  'panel.octohelper.com',
];

export function safeRedirect(url: string): void {
  try {
    const parsed = new URL(url);
    if (!ALLOWED_REDIRECT_HOSTS.some(h => parsed.hostname === h || parsed.hostname.endsWith('.' + h))) {
      console.error('Blocked redirect to untrusted domain:', parsed.hostname);
      return;
    }
    window.location.href = url;
  } catch {
    console.error('Invalid redirect URL');
  }
}
