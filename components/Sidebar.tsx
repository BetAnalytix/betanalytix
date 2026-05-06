'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'

const navItems = [
  { href: '/', icon: '📊', label: 'Dashboard' },
  { href: '/history', icon: '📋', label: 'Historique' },
  { href: '/settings', icon: '⚙️', label: 'Paramètres' },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside style={{
      width: 240,
      background: 'var(--bg)',
      borderRight: '1px solid var(--border2)',
      display: 'flex',
      flexDirection: 'column',
      position: 'fixed',
      top: 0, left: 0, bottom: 0,
      zIndex: 100,
    }}>
      <div style={{ padding: '40px 32px 32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--green)' }} />
          <div style={{ fontSize: 14, fontWeight: 700, letterSpacing: '0.05em', color: 'var(--text)', textTransform: 'uppercase' }}>
            BetAnalytix
          </div>
        </div>
      </div>

      <nav style={{ padding: '0 16px', flex: 1 }}>
        {navItems.map(item => {
          const active = pathname === item.href
          return (
            <Link key={item.href} href={item.href} style={{ textDecoration: 'none' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 16px',
                borderRadius: 8,
                cursor: 'pointer',
                color: active ? 'var(--text)' : 'var(--text2)',
                background: active ? 'var(--bg2)' : 'transparent',
                fontSize: 13,
                fontWeight: active ? 600 : 400,
                marginBottom: 4,
                transition: 'all 0.2s',
              }}>
                <span style={{ opacity: active ? 1 : 0.5 }}>{item.icon}</span>
                {item.label}
              </div>
            </Link>
          )
        })}
      </nav>

      <div style={{ padding: '32px', fontSize: 10, color: 'var(--text3)', letterSpacing: '0.05em' }}>
        v0.1.0 INSTITUTIONAL
      </div>
    </aside>
  )
}
