'use client'

import { useState } from 'react'

interface TopBarProps {
  title: string
  liveCount?: number
}

export default function TopBar({ title, liveCount = 0 }: TopBarProps) {
  const [search, setSearch] = useState('')

  return (
    <div style={{
      height: 64,
      background: 'var(--bg2)',
      borderBottom: '1px solid var(--border2)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 32px',
      gap: 16,
      position: 'sticky',
      top: 0, zIndex: 90,
    }}>
      <div style={{ fontFamily: 'Syne, sans-serif', fontSize: 20, fontWeight: 800, flex: 1 }}>
        {title}
      </div>

      {liveCount > 0 && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: 'rgba(248,113,113,0.1)', border: '1px solid rgba(248,113,113,0.3)',
          padding: '6px 12px', borderRadius: 8,
          fontFamily: 'DM Mono, monospace', fontSize: 11, color: 'var(--red)',
        }}>
          <span className="animate-pulse-dot" style={{
            width: 6, height: 6, background: 'var(--red)', borderRadius: '50%', display: 'inline-block',
          }} />
          LIVE · {liveCount} matchs
        </div>
      )}

      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        background: 'var(--bg3)', border: '1px solid var(--border2)',
        borderRadius: 10, padding: '8px 14px', width: 260,
      }}>
        <span>🔍</span>
        <input
          type="text"
          placeholder="Rechercher équipe, ligue..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            background: 'none', border: 'none', outline: 'none',
            color: 'var(--text)', fontSize: 13, width: '100%',
          }}
        />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{
          width: 36, height: 36, background: 'var(--bg3)',
          border: '1px solid var(--border2)', borderRadius: 8,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', fontSize: 15, position: 'relative',
        }}>
          🔔
          <span style={{
            position: 'absolute', top: 6, right: 6,
            width: 7, height: 7, background: 'var(--green)',
            borderRadius: '50%', border: '1.5px solid var(--bg2)',
          }} />
        </div>
        <div style={{
          width: 36, height: 36, background: 'var(--bg3)',
          border: '1px solid var(--border2)', borderRadius: 8,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', fontSize: 15,
        }}>📤</div>
        <button style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          padding: '6px 12px', borderRadius: 8, fontSize: 12,
          fontWeight: 600, cursor: 'pointer', border: 'none',
          background: 'var(--green2)', color: '#000',
        }}>+ Analyser</button>
      </div>
    </div>
  )
}
