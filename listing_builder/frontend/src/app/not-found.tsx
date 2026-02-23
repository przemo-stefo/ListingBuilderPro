// frontend/src/app/not-found.tsx
// Purpose: Custom 404 page — clear message instead of redirect to /login
// NOT for: Error boundaries (that would be error.tsx)

import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
      <div className="text-center space-y-4">
        <p className="text-6xl font-bold text-gray-700">404</p>
        <h1 className="text-xl font-semibold text-white">Strona nie została znaleziona</h1>
        <p className="text-sm text-gray-500">Sprawdź adres URL lub wróć na stronę główną.</p>
        <Link
          href="/"
          className="inline-block mt-4 rounded-lg bg-emerald-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-emerald-400 transition-colors"
        >
          Strona główna
        </Link>
      </div>
    </div>
  )
}
