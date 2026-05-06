import Sidebar from '@/components/Sidebar'
import MatchCard from '@/components/MatchCard'
import { getTodayMatches } from '@/lib/football-api'
import { generatePrediction } from '@/lib/predictions'
import { supabase } from '@/lib/supabase'
import Link from 'next/link'

export const revalidate = 300

async function getDashboardData(date?: string) {
  try {
    const matches = await getTodayMatches(date)
    const predictions = await Promise.all(
      matches.map((m) => generatePrediction(m))
    )

    const { data: { session } } = await supabase.auth.getSession()
    let balance = 1000
    if (session?.user) {
      const { data: profile } = await supabase
        .from('profiles')
        .select('balance')
        .eq('id', session.user.id)
        .single()
      if (profile) balance = profile.balance
    }

    return { matches, predictions, balance }
  } catch (error) {
    console.error("Dashboard error:", error)
    return { matches: [], predictions: [], balance: 1000 }
  }
}

interface PageProps {
  searchParams: { date?: string }
}

export default async function DashboardPage({ searchParams }: PageProps) {
  const todayStr = new Date().toISOString().split('T')[0]
  const tomorrowStr = new Date(Date.now() + 86400000).toISOString().split('T')[0]
  const selectedDate = searchParams.date || todayStr

  const { matches, predictions, balance } = await getDashboardData(selectedDate)

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg)' }}>
      <Sidebar />

      <main style={{ marginLeft: 240, flex: 1, display: 'flex', flexDirection: 'column' }}>
        
        {/* Header Institutionnel */}
        <header style={{ 
          height: 80, 
          padding: '0 48px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--border2)',
          background: 'var(--bg)',
          position: 'sticky',
          top: 0,
          zIndex: 10
        }}>
          <h1 style={{ fontSize: 16, fontWeight: 700, letterSpacing: '-0.02em' }}>
            {selectedDate === todayStr ? 'Market Overview' : `Forecast: ${selectedDate}`}
          </h1>

          <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
            {/* Date Selector */}
            <div style={{ display: 'flex', gap: 8, background: 'var(--bg2)', padding: 4, borderRadius: 8 }}>
              {[
                { label: "Today", date: todayStr },
                { label: "Tomorrow", date: tomorrowStr },
              ].map((tab) => {
                const active = selectedDate === tab.date
                return (
                  <Link key={tab.date} href={`/?date=${tab.date}`} style={{ textDecoration: 'none' }}>
                    <div style={{
                      padding: '6px 16px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                      background: active ? 'var(--bg3)' : 'transparent',
                      color: active ? 'var(--text)' : 'var(--text2)',
                      transition: '0.2s'
                    }}>{tab.label}</div>
                  </Link>
                )
              })}
            </div>

            {/* Balance */}
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 10, color: 'var(--text3)', textTransform: 'uppercase', marginBottom: 2 }}>Available Balance</div>
              <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text)' }}>
                {balance.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
              </div>
            </div>
          </div>
        </header>

        {/* Content Section */}
        <div style={{ padding: '40px 48px', flex: 1 }}>
          
          <div style={{ maxWidth: 1000, margin: '0 auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 32 }}>
              <div style={{ fontSize: 14, fontWeight: 600 }}>Active Predictions</div>
              <div style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, background: 'var(--bg2)', border: '1px solid var(--border2)', color: 'var(--text3)' }}>
                {matches.length} matches found
              </div>
            </div>

            {/* Match List (Professional Table Look) */}
            <div style={{ 
              background: 'var(--bg)', 
              border: '1px solid var(--border2)', 
              borderRadius: 12,
              overflow: 'hidden'
            }}>
              {matches.length === 0 ? (
                <div style={{ padding: 80, textAlign: 'center', color: 'var(--text3)', fontSize: 13 }}>
                  No high-probability opportunities detected for this period.
                </div>
              ) : (
                matches.map((match, i) => (
                  <MatchCard key={match.id} match={match} prediction={predictions[i]} />
                ))
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  )
}
