import type { Match } from '@/lib/football-api'
import type { PredictionResult } from '@/lib/predictions'

interface ValueBetsPanelProps {
  matches: Match[]
  predictions: PredictionResult[]
}

export default function ValueBetsPanel({ matches, predictions }: ValueBetsPanelProps) {
  const valueBets = predictions
    .filter(p => p.isValueBet)
    .map(p => ({
      pred: p,
      match: matches.find(m => m.id === p.matchId),
    }))
    .filter(v => v.match)
    .slice(0, 3)

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(251,191,36,0.08), rgba(251,191,36,0.03))',
      border: '1px solid rgba(251,191,36,0.25)',
      borderRadius: 14, padding: 18,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <div style={{
          width: 32, height: 32, background: 'var(--gold-dim)',
          borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
        }}>⚡</div>
        <div>
          <div style={{ fontFamily: 'Syne, sans-serif', fontSize: 13, fontWeight: 700, color: 'var(--gold)' }}>
            Value Bets Actives
          </div>
          <div style={{ fontFamily: 'DM Mono, monospace', fontSize: 10, color: 'var(--text3)' }}>
            {valueBets.length} opportunité{valueBets.length !== 1 ? 's' : ''} détectée{valueBets.length !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {valueBets.length === 0 && (
        <div style={{ textAlign: 'center', padding: 24, color: 'var(--text3)', fontFamily: 'DM Mono, monospace', fontSize: 12 }}>
          Aucune value bet détectée aujourd&apos;hui
        </div>
      )}

      {valueBets.map(({ pred, match }, i) => (
        <div key={i} style={{
          background: 'rgba(0,0,0,0.2)', borderRadius: 10, padding: 12, marginBottom: 8,
          border: '1px solid rgba(251,191,36,0.1)',
        }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>
            {match!.leagueFlag} {match!.homeTeam} vs {match!.awayTeam}
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {[
              { label: `Prob: ${pred.prediction === '1' ? pred.probHome : pred.prediction === 'X' ? pred.probDraw : pred.probAway}%`, highlight: false },
              { label: `Cote: ${pred.recommendedOdds}`, highlight: false },
              { label: `+${pred.valuePct}% value`, highlight: true },
            ].map((s, j) => (
              <span key={j} style={{
                fontFamily: 'DM Mono, monospace', fontSize: 10, padding: '3px 7px', borderRadius: 4,
                background: s.highlight ? 'var(--gold-dim)' : 'var(--bg3)',
                color: s.highlight ? 'var(--gold)' : 'var(--text2)',
              }}>{s.label}</span>
            ))}
          </div>
        </div>
      ))}

      <button style={{
        width: '100%', marginTop: 8,
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
        padding: '9px 16px', borderRadius: 8, fontSize: 13, fontWeight: 600,
        cursor: 'pointer', border: 'none', background: 'var(--green2)', color: '#000',
      }}>
        ⚡ Voir toutes les value bets
      </button>
    </div>
  )
}
