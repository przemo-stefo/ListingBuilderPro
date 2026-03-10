// frontend/src/app/share/[token]/page.tsx
// Purpose: Public page displaying a shared listing snapshot
// NOT for: Editing or re-optimizing (read-only view)

import { Metadata } from 'next'
import SharedListingView from './SharedListingView'

interface Props {
  params: Promise<{ token: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { token } = await params
  return {
    title: `Shared Listing | OctoHelper`,
    description: 'Podglad udostepnionego listingu z OctoHelper Optimizer',
    robots: 'noindex, nofollow',
  }
}

export default async function SharePage({ params }: Props) {
  const { token } = await params
  return <SharedListingView token={token} />
}
