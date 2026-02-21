// frontend/src/components/landing/MarketplaceLogos.tsx
// Purpose: Reusable marketplace logo row for landing page sections
// NOT for: Logo management or marketplace config

import Image from 'next/image'

const LOGOS = [
  { src: '/logos/amazon.svg', alt: 'Amazon', width: 100 },
  { src: '/logos/allegro.svg', alt: 'Allegro', width: 100 },
  { src: '/logos/ebay.svg', alt: 'eBay', width: 70 },
  { src: '/logos/kaufland.svg', alt: 'Kaufland', width: 110 },
  { src: '/logos/temu.svg', alt: 'Temu', width: 75 },
  { src: '/logos/aliexpress.svg', alt: 'AliExpress', width: 120 },
  { src: '/logos/bol.svg', alt: 'Bol.com', width: 70 },
]

interface Props {
  label?: string
  className?: string
}

export function MarketplaceLogos({ label, className = '' }: Props) {
  return (
    <div className={`flex flex-col items-center gap-4 ${className}`}>
      {label && (
        <span className="text-xs font-medium uppercase tracking-widest text-gray-500">{label}</span>
      )}
      <div className="flex items-center justify-center gap-8 sm:gap-12 flex-wrap opacity-50 hover:opacity-70 transition-opacity">
        {LOGOS.map((logo) => (
          <Image
            key={logo.alt}
            src={logo.src}
            alt={logo.alt}
            width={logo.width}
            height={36}
            className="h-7 w-auto brightness-0 invert"
          />
        ))}
      </div>
    </div>
  )
}
