const recentResults = ['win','win','loss','win','win','draw','win','win','loss','win'] as const

const resultStyle = {
  win: { bg: 'var(--green-dim)', color: 'var(--green)', border: 'var(--border)', label: '✓' },
  draw: { bg: 'var(--gold-dim)', color: 'var(--gold)', border: 'rgba(251,191,36,0.3)', label: '—' },
  loss: { bg: 'var(--red-dim)', color: 'var(--red)', border: 'rgba(248,113,113,0.3)', label: '✗' },
}

export default function ModelAccuracy() {
  const accuracy = 68.4
  const circumference = 2 * Math.PI * 50
  const offset = circumference - (accuracy / 100) * circumference

  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--border2)', borderRadius: 14, padding: 18 }}>
      <div style={{ fontFamily: 'Syne, sans-serif', fontSize: 15, fontWeight: 700, marginBottom: 2 }}>
        🧠 Précision du Modèle IA
      </div>
      <span style={{ fontFamily: 'DM Mono, monospace', fontSize: 10, color: 'var(--text3)' }}>
        Basé sur 2,847 prédictions
      </span>

      {/* Circular progress */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '16px 0', position: 'relative' }}>
        <svg width="120" height="120" viewBox="0 0 120 120" style={{ transform: 'rotate(-90deg)' }}>
          <circle cx="60" cy="60" r="50" fill="none" stroke="var(--bg3)" strokeWidth="8" />
          <circle
            cx="60" cy="60" r="50" fill="none"
            stroke="var(--green)" strokeWidth="8" strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 1s ease' }}
          />
        </svg>
        <div style={{ position: 'absolute', textAlign: 'center' }}>
          <span style={{ fontFamily: 'Syne, sans-serif', fontSize: 22, fontWeight: 800, color: 'var(--green)', display: 'block' }}>
            {accuracy}%
          </span>
          <span style={{ fontFamily: 'DM Mono, monospace', fontSize: 9, color: 'var(--text3)' }}>Précision</span>
        </div>
      </div>

      {/* Accuracy grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {[
          { label: 'Haute confiance', val: '74.2%', color: 'var(--green)' },
          { label: 'Moy. confiance', val: '61.8%', color: 'var(--gold)' },
          { label: 'Premier League', val: '71.3%', color: 'var(--green)' },
          { label: 'Champions L.', val: '66.9%', color: 'var(--green)' },
        ].map((item, i) => (
          <div key={i} style={{ background: 'var(--bg3)', borderRadius: 8, padding: 10, border: '1px solid var(--border2)' }}>
            <div style={{ fontFamily: 'DM Mono, monospace', fontSize: 9, color: 'var(--text3)', marginBottom: 4, textTransform: 'uppercase' }}>
              {item.label}
            </div>
            <div style={{ fontFamily: 'Syne, sans-serif', fontSize: 18, fontWeight: 800, color: item.color }}>
              {item.val}
            </div>
          </div>
        ))}
      </div>

      <div style={{ height: 1, background: 'var(--border2)', margin: '12px 0' }} />

      <div style={{ fontFamily: 'DM Mono, monospace', fontSize: 10, color: 'var(--text3)', marginBottom: 8 }}>
        Derniers résultats du modèle
      </div>
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        {recentResults.map((r, i) => {
          const s = resultStyle[r]
          return (
            <div key={i} style={{
              width: 28, height: 28, borderRadius: 6,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: 'DM Mono, monospace', fontSize: 11, fontWeight: 700,
              background: s.bg, color: s.color, border: `1px solid ${s.border}`,
            }}>{s.label}</div>
          )
        })}
      </div>
    </div>
  )
}
