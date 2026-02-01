// src/lib/landing-data.ts
// Purpose: All static data for the landing page sections
// NOT for: Component logic or styling

export const navLinks = [
  { label: 'Features', href: '#features' },
  { label: 'Pricing', href: '#pricing' },
  { label: 'How It Works', href: '#how-it-works' },
];

export const radarItems = [
  { label: 'EPR Packaging DE – Registered & Compliant', status: 'green' as const },
  { label: 'WEEE FR – Q2 Report Due in 14 Days', status: 'yellow' as const },
  { label: 'Battery Registration IT – Missing – High Block Risk', status: 'red' as const },
];

export const painPoints = [
  { icon: 'Eye', title: 'Hidden Listings', description: 'Your products disappear from search without warning' },
  { icon: 'ShoppingCart', title: 'Lost Buy Box', description: 'Non-compliant sellers lose priority placement' },
  { icon: 'Ban', title: 'Account Suspension', description: 'Complete selling privileges revoked overnight' },
  { icon: 'CreditCard', title: 'Frozen Payouts', description: 'Funds held indefinitely during compliance review' },
];

export const steps = [
  { number: '01', icon: 'ScanSearch', title: 'Analyze Your Listings', description: 'Upload your SKUs or connect your marketplace accounts. We scan product categories, attributes, and sales data.' },
  { number: '02', icon: 'Brain', title: 'AI Classification', description: 'Our AI determines WEEE, Battery, and Packaging obligations per country – including local exceptions and edge cases.' },
  { number: '03', icon: 'Shield', title: 'Risk Assessment', description: 'Cross-reference with legal requirements and marketplace enforcement patterns. Get a clear risk score.' },
  { number: '04', icon: 'Zap', title: 'Actionable Alerts', description: 'Receive specific next steps: register here, submit this report, update that field. No legal jargon.' },
];

export const features = [
  { icon: 'Radar', badge: 'Core', title: 'Compliance Radar', description: 'Real-time risk status for every SKU. Traffic light system: green (OK), yellow (attention), red (high risk).' },
  { icon: 'TrendingUp', badge: 'Intelligence', title: 'Enforcement Tracker', description: 'Know where marketplaces are actively enforcing. Amazon DE: aggressive. eBay: delayed. Kaufland: selective.' },
  { icon: 'FileText', badge: 'Automation', title: 'Reporting Guardian', description: 'Never miss a deadline. Track report due dates and weight thresholds across all EPR schemes.' },
  { icon: 'Timer', badge: 'Roadmap', title: 'Compliance Timeline', description: 'Visual timeline showing registration dates, report deadlines, and predicted risk windows.' },
  { icon: 'Globe', badge: 'EU-Wide', title: 'Multi-Country Coverage', description: "Germany, France, Poland and expanding. Each country's local rules and exceptions handled." },
  { icon: 'BarChart3', badge: 'Forecast', title: 'Threshold Simulator', description: "Predict when you'll cross weight thresholds. Plan registrations before obligations kick in." },
];

export const marketplaceAlerts = [
  { icon: 'AlertTriangle', title: 'Listing Suspension Alert', description: 'Instant notification when your listing is at risk of being hidden or suspended due to missing EPR data.' },
  { icon: 'Shield', title: 'Account Health Warning', description: 'Monitor your seller account health score and get alerts before it drops to critical levels.' },
  { icon: 'ShoppingCart', title: 'Buy Box Loss Alert', description: 'Know immediately when compliance issues threaten your Buy Box position on Amazon.' },
  { icon: 'FileWarning', title: 'Policy Violation Notice', description: 'Early warning when marketplace policy changes affect your products or categories.' },
  { icon: 'Battery', title: 'WEEE/Battery Compliance', description: 'Alerts for missing WEEE registration or battery compliance requirements per country.' },
  { icon: 'Bell', title: 'Report Deadline Reminder', description: 'Automated reminders 30, 14, and 7 days before quarterly and annual EPR report deadlines.' },
];

export const ecommerceAlerts = [
  { icon: 'Store', title: 'Shopify/WooCommerce Sync', description: 'Real-time compliance monitoring for your online store products across all EU markets.' },
  { icon: 'Receipt', title: 'VAT Threshold Alert', description: "Notifications when you're approaching VAT registration thresholds in new countries." },
  { icon: 'Truck', title: 'Shipping Compliance', description: 'Alerts for cross-border shipping requirements, packaging regulations, and customs issues.' },
  { icon: 'ShieldAlert', title: 'Product Safety Notice', description: 'Warnings about product safety standards, CE marking, and GPSR requirements.' },
  { icon: 'Package', title: 'Packaging Weight Tracker', description: 'Track cumulative packaging weight and get alerts before crossing EPR thresholds.' },
  { icon: 'Globe', title: 'New Market Expansion', description: 'Compliance checklist alerts when you start selling to a new EU country.' },
];

export const comparisonRows = [
  { aspect: 'Focus', traditional: 'EPR Registration', guard: 'Risk Monitoring & Prevention' },
  { aspect: 'Approach', traditional: 'Spreadsheets & Email', guard: 'AI + Automated Scoring' },
  { aspect: 'Coverage', traditional: 'Single Marketplace', guard: 'Multi-Marketplace' },
  { aspect: 'Timing', traditional: 'Reactive (After Problems)', guard: 'Proactive (Before Blocking)' },
  { aspect: 'Insight', traditional: 'Registration Status Only', guard: 'Enforcement Intelligence' },
];

export const pricingTiers = [
  {
    name: 'Starter',
    subtitle: 'For sellers starting with compliance',
    price: 29,
    features: ['1 Marketplace', '1 Country (DE, FR, or PL)', 'Up to 100 SKUs', 'Weekly risk reports', 'Email alerts'],
    cta: 'Start Free Trial',
    popular: false,
  },
  {
    name: 'Pro',
    subtitle: 'For growing cross-border sellers',
    price: 79,
    features: ['All Marketplaces', '5 Countries', 'Unlimited SKUs', 'Daily risk monitoring', 'Enforcement tracker', 'Threshold simulator', 'Priority support'],
    cta: 'Start Free Trial',
    popular: true,
  },
  {
    name: 'Agency',
    subtitle: 'For agencies managing multiple sellers',
    price: 199,
    features: ['Everything in Pro', 'Unlimited clients', 'White-label reports', 'API access', 'Bulk CSV import', 'Dedicated success manager', 'Custom integrations'],
    cta: 'Contact Sales',
    popular: false,
  },
];

export const footerLinks = {
  Product: [
    { label: 'Features', href: '#features' },
    { label: 'Pricing', href: '#pricing' },
    { label: 'Integrations', href: '#' },
    { label: 'Changelog', href: '#' },
  ],
  Company: [
    { label: 'About', href: '#' },
    { label: 'Blog', href: '#' },
    { label: 'Careers', href: '#' },
    { label: 'Contact', href: '#' },
  ],
  Legal: [
    { label: 'Privacy Policy', href: '#' },
    { label: 'Terms of Service', href: '#' },
    { label: 'GDPR', href: '#' },
    { label: 'Imprint', href: '#' },
  ],
  Support: [
    { label: 'Documentation', href: '#' },
    { label: 'API Reference', href: '#' },
    { label: 'Status', href: '#' },
    { label: 'Help Center', href: '#' },
  ],
};
