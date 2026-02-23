// frontend/src/app/privacy/page.tsx
// Purpose: Privacy Policy page — required for Amazon SP-API production approval
// NOT for: Cookie consent UI or GDPR opt-in flows

export default function PrivacyPolicyPage() {
  return (
    <div className="max-w-3xl mx-auto py-8">
      <h1 className="text-3xl font-bold text-white mb-6">Privacy Policy</h1>
      <p className="text-neutral-400 mb-8">Last updated: February 12, 2026</p>

      <div className="space-y-8 text-neutral-300 leading-relaxed">
        <section>
          <h2 className="text-xl font-semibold text-white mb-3">1. Who We Are</h2>
          <p>
            VIAREGIA.ONLINE Sp. z o.o. (&quot;we&quot;, &quot;us&quot;, &quot;our&quot;) operates the
            OctoHelper platform at panel.octohelper.com. We are
            a company registered in Poland (NIP: 5252944772).
          </p>
          <p className="mt-2">
            Contact: kontakt@octohelper.com
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">2. What Data We Collect</h2>
          <p>We collect the following data when you use our services:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Account information (email address, name) when you register</li>
            <li>Marketplace connection data when you authorize your seller accounts (Amazon, Kaufland, Allegro, eBay)</li>
            <li>Product monitoring data (ASINs, prices, stock levels, reviews) from connected marketplaces</li>
            <li>Usage data (pages visited, features used) for service improvement</li>
            <li>Technical data (IP address, browser type) from server logs</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">3. Amazon Selling Partner API Data</h2>
          <p>
            When you connect your Amazon Seller account, we access data through the
            Amazon Selling Partner API (SP-API) under your authorization. This includes:
          </p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Product catalog and listing information</li>
            <li>Pricing and competitive pricing data</li>
            <li>Inventory levels and stock status</li>
          </ul>
          <p className="mt-2">
            We use this data solely to provide monitoring, alerts, and compliance
            analysis services as described in our Terms of Service. We do not sell,
            share, or transfer your Amazon data to third parties. Your Amazon data is
            stored securely and deleted within 30 days of account termination.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">4. How We Use Your Data</h2>
          <ul className="list-disc list-inside space-y-1">
            <li>To provide product monitoring, price tracking, and compliance alerts</li>
            <li>To generate reports and analytics for your marketplace accounts</li>
            <li>To send alert notifications (email, webhook) when issues are detected</li>
            <li>To improve our services and fix technical issues</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">5. Data Storage and Security</h2>
          <p>
            Your data is stored in secure PostgreSQL databases hosted by Supabase
            (AWS eu-central-1). All data is encrypted in transit (TLS 1.2+) and at
            rest. API credentials and tokens are stored encrypted and never exposed
            in logs or responses.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">6. Data Retention</h2>
          <ul className="list-disc list-inside space-y-1">
            <li>Account data: retained while your account is active</li>
            <li>Monitoring snapshots: retained for 12 months</li>
            <li>Alert history: retained for 6 months</li>
            <li>Marketplace API tokens: deleted within 24 hours of disconnection</li>
            <li>All data deleted within 30 days of account termination upon request</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">7. Your Rights (GDPR)</h2>
          <p>If you are in the European Economic Area, you have the right to:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Access your personal data</li>
            <li>Rectify inaccurate data</li>
            <li>Request deletion of your data</li>
            <li>Export your data in a portable format</li>
            <li>Object to processing of your data</li>
            <li>Withdraw consent at any time</li>
          </ul>
          <p className="mt-2">
            To exercise these rights, contact us at kontakt@octohelper.com.
            We will respond within 30 days.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">8. Cookies</h2>
          <p>
            We use only essential cookies required for authentication and session
            management. We do not use advertising or tracking cookies.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">9. Third-Party Services</h2>
          <ul className="list-disc list-inside space-y-1">
            <li>Supabase (database hosting, EU region)</li>
            <li>Vercel (frontend hosting)</li>
            <li>Render (backend hosting)</li>
            <li>Groq (LLM processing — no personal data sent)</li>
            <li>Keepa (Amazon product data — public data only)</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">10. Changes to This Policy</h2>
          <p>
            We may update this policy from time to time. We will notify you of
            significant changes via email or in-app notification. Continued use of
            our services after changes constitutes acceptance.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">11. Contact</h2>
          <p>
            For privacy-related questions or requests:<br />
            VIAREGIA.ONLINE Sp. z o.o.<br />
            kontakt@octohelper.com
          </p>
        </section>
      </div>
    </div>
  )
}
