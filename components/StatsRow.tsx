interface Stat {
  icon: string
  label: string
  value: string
  valueColor?: string
  change: string
  changeUp?: boolean
}

interface StatsRowProps {
  stats: Stat[]
}

export default function StatsRow({ stats }: StatsRowProps) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: 16,
      marginBottom: 28,
    }}>
      {stats.map((stat, i) => (
        <div key={i} className="animate-fade-in" style={{
          background: 'var(--card)', border: '1px solid var(--border2)',
          borderRadius: 14, padding: 20, position: 'relative', overflow: 'hidden',
        }}>
          <div style={{
            position: 'absolute', top: 0, right: 0,
            width: 80, height: 80, borderRadius: '50%',
            opacity: 0.06, background: 'var(--green)',
            transform: 'translate(20px, -20px)',
          }} />
          <div style={{ position: 'absolute', top: 20, right: 20, fontSize: 20, opacity: 0.4 }}>
            {stat.icon}
          </div>
          <div style={{ fontFamily: 'DM Mono, monospace', fontSize: 10, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
            {stat.label}
          </div>
          <div style={{ fontFamily: 'Syne, sans-serif', fontSize: 28, fontWeight: 800, color: stat.valueColor ?? 'var(--text)', lineHeight: 1, marginBottom: 8 }}>
            {stat.value}
          </div>
          <div style={{
            fontFamily: 'DM Mono, monospace', fontSize: 11,
            color: stat.changeUp === undefined ? 'var(--text3)' : stat.changeUp ? 'var(--green)' : 'var(--red)',
            display: 'flex', alignItems: 'center', gap: 4,
          }}>
            {stat.changeUp !== undefined && (stat.changeUp ? '↑' : '↓')} {stat.change}
          </div>
        </div>
      ))}
    </div>
  )
}
