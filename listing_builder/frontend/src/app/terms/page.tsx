// frontend/src/app/terms/page.tsx
// Purpose: Terms of Service page — required for Amazon SP-API production approval
// NOT for: Subscription billing terms or SLA definitions

export default function TermsOfServicePage() {
  return (
    <div className="max-w-3xl mx-auto py-8">
      <h1 className="text-3xl font-bold text-white mb-6">Terms of Service</h1>
      <p className="text-neutral-400 mb-8">Last updated: February 12, 2026</p>

      <div className="space-y-8 text-neutral-300 leading-relaxed">
        <section>
          <h2 className="text-xl font-semibold text-white mb-3">1. Service Description</h2>
          <p>
            VIAREGIA.ONLINE Sp. z o.o. (&quot;we&quot;, &quot;us&quot;) provides the OctoHelper
            platform — a marketplace listing optimization and monitoring tool for e-commerce
            sellers. Our services include:
          </p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Product monitoring across Amazon, Kaufland, Allegro, and eBay</li>
            <li>Price tracking, Buy Box monitoring, and stock level alerts</li>
            <li>Listing compliance analysis and policy violation detection</li>
            <li>News aggregation for marketplace policy changes</li>
            <li>Listing optimization and keyword analysis tools</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">2. Account Registration</h2>
          <p>
            To use our services, you must create an account and provide accurate
            information. You are responsible for maintaining the security of your
            account credentials and for all activities under your account.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">3. Marketplace Connections</h2>
          <p>
            When you connect your marketplace seller accounts (Amazon, Kaufland,
            Allegro, eBay) to our platform, you authorize us to access your account
            data as described in our Privacy Policy. You may disconnect your
            marketplace accounts at any time. We will delete associated tokens
            within 24 hours of disconnection.
          </p>
          <p className="mt-2">
            You represent that you have the authority to grant us access to your
            marketplace accounts and that doing so does not violate any agreements
            with the respective marketplace operators.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">4. Acceptable Use</h2>
          <p>You agree not to:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Use our services for any unlawful purpose</li>
            <li>Attempt to access other users&apos; data or accounts</li>
            <li>Reverse engineer, decompile, or disassemble our software</li>
            <li>Use our API beyond reasonable rate limits</li>
            <li>Resell or redistribute our services without authorization</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">5. Data Accuracy</h2>
          <p>
            We strive to provide accurate marketplace data, but we cannot guarantee
            100% accuracy or real-time data. Monitoring data may be delayed depending
            on marketplace API availability and polling intervals. You should not
            rely solely on our data for critical business decisions without
            independent verification.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">6. Service Availability</h2>
          <p>
            We aim for high availability but do not guarantee uninterrupted service.
            We may perform maintenance, updates, or experience downtime due to
            third-party services (marketplace APIs, hosting providers). We will
            notify users of planned maintenance when possible.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">7. Intellectual Property</h2>
          <p>
            All content, software, and technology comprising the OctoHelper
            platform is owned by VIAREGIA.ONLINE Sp. z o.o. You retain ownership of your
            marketplace data. By using our services, you grant us a limited license
            to process your data solely for providing the services described herein.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">8. Limitation of Liability</h2>
          <p>
            To the maximum extent permitted by law, VIAREGIA.ONLINE Sp. z o.o. shall not be
            liable for any indirect, incidental, special, consequential, or punitive
            damages, including loss of profits, data, or business opportunities,
            arising from your use of our services. Our total liability shall not
            exceed the amount you paid us in the 12 months preceding the claim.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">9. Termination</h2>
          <p>
            You may terminate your account at any time by contacting us. We may
            suspend or terminate your account if you violate these terms. Upon
            termination, we will delete your data within 30 days as described in
            our Privacy Policy.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">10. Changes to Terms</h2>
          <p>
            We may update these terms from time to time. We will notify you of
            material changes via email. Continued use of our services after changes
            take effect constitutes acceptance of the updated terms.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">11. Governing Law</h2>
          <p>
            These terms are governed by the laws of the Republic of Poland.
            Any disputes shall be resolved by the competent courts in Warsaw,
            Poland.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">12. Contact</h2>
          <p>
            For questions about these terms:<br />
            VIAREGIA.ONLINE Sp. z o.o.<br />
            kontakt@octohelper.com
          </p>
        </section>
      </div>
    </div>
  )
}
