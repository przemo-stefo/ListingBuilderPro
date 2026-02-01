// dashboard/tailwind.config.ts
// Purpose: Tailwind CSS configuration for Compliance Guard dashboard
// NOT for: Application logic

import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Dark mode palette (from David's preferences)
        background: '#121212',
        foreground: '#ffffff',
        card: '#1A1A1A',
        'card-foreground': '#ffffff',
        border: '#333333',
        'border-secondary': '#2C2C2C',
        muted: '#262626',
        'muted-foreground': '#a3a3a3',

        // Status colors
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444',
        info: '#3b82f6',

        // Health score gradient
        'health-excellent': '#22c55e',
        'health-good': '#84cc16',
        'health-warning': '#f59e0b',
        'health-danger': '#ef4444',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}

export default config
