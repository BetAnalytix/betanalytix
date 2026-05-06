import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'BetAnalytix — IA de Prédiction Sportive',
  description: 'Prédictions sportives alimentées par IA',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  )
}
