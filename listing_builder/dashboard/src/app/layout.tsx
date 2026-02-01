// src/app/layout.tsx
// Purpose: Root layout - minimal shell for all pages
// NOT for: Page-specific layouts (see dashboard/layout.tsx)

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Compliance Guard - AI Marketplace Protection',
  description: 'Stop marketplace blocking before it starts. AI-powered compliance monitoring for Amazon, eBay, Allegro, Kaufland, and more.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}
