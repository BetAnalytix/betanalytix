export default function TelegramPanel() {
  return (
    <div style={{
      background: '#1e3a5f',
      border: '1px solid rgba(96,165,250,0.3)',
      borderRadius: 14, padding: 16,
      fontFamily: 'DM Mono, monospace',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <div style={{
          width: 32, height: 32, background: '#2196f3',
          borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
        }}>✈️</div>
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--blue)' }}>BetAnalytix Bot</div>
          <div style={{ fontSize: 10, color: 'var(--text3)' }}>@betanalytix_bot · En ligne</div>
        </div>
      </div>

      <div style={{
        background: 'rgba(255,255,255,0.05)', borderRadius: 10, padding: 12,
        fontSize: 11, lineHeight: 1.7, color: 'var(--text)',
      }}>
        <span style={{ fontSize: 13 }}>⚡</span> <strong>VALUE BET DÉTECTÉE</strong><br /><br />
        ⚽ <strong>Man City vs Arsenal</strong><br />
        📊 Notre probabilité: <strong style={{ color: 'var(--green)' }}>58%</strong><br />
        📈 Cote bookmaker: <strong style={{ color: 'var(--gold)' }}>1.85</strong><br />
        💰 Value: <strong style={{ color: 'var(--green)' }}>+12%</strong><br />
        🎯 Confiance: <strong>72%</strong><br />
        ⏰ Match dans <strong>2h30</strong><br /><br />
        <span style={{ color: 'var(--blue)' }}>→ Voir l&apos;analyse complète</span>
      </div>

      <button style={{
        width: '100%', marginTop: 12,
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
        padding: '6px 12px', borderRadius: 8, fontSize: 12, fontWeight: 600,
        cursor: 'pointer',
        background: 'transparent',
        border: '1px solid rgba(96,165,250,0.3)',
        color: 'var(--blue)',
      }}>
        🤖 Configurer les alertes
      </button>
    </div>
  )
}
