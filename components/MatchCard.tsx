'use client'

import { useState } from 'react'
import type { Match } from '@/lib/football-api'
import type { PredictionResult } from '@/lib/predictions'

interface MatchCardProps {
  match: Match
  prediction: PredictionResult
  delay?: number
}

export default function MatchCard({ match, prediction }: MatchCardProps) {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        padding: '24px 32px',
        background: isHovered ? 'var(--bg2)' : 'transparent',
        borderBottom: '1px solid var(--border2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        transition: 'all 0.2s ease',
        cursor: 'pointer'
      }}
    >
      {/* Teams Section */}
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--text)', letterSpacing: '-0.02em' }}>
          {match.homeTeam} <span style={{ color: 'var(--text3)', fontWeight: 400, margin: '0 8px' }}>/</span> {match.awayTeam}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {match.league} • {match.matchTime}
        </div>
      </div>

      {/* Stats Section */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 48 }}>
        
        {/* Kelly Stake */}
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 10, color: 'var(--text3)', textTransform: 'uppercase', marginBottom: 4 }}>Mise Kelly</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--gold)' }}>
            {prediction.recommendedStake ? `${prediction.recommendedStake}$` : '--'}
          </div>
        </div>

        {/* Confidence Badge */}
        <div style={{ 
          width: 44, height: 44, 
          borderRadius: '50%', 
          border: `2px solid ${prediction.confidence >= 70 ? 'var(--green)' : 'var(--border2)'}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 13, fontWeight: 800, color: prediction.confidence >= 70 ? 'var(--green)' : 'var(--text2)'
        }}>
          {prediction.confidence}%
        </div>

        {/* Action Button (Hover only) */}
        <div style={{ width: 100, display: 'flex', justifyContent: 'flex-end' }}>
          {isHovered && (
            <button style={{
              background: 'var(--text)',
              color: 'var(--bg)',
              border: 'none',
              borderRadius: 6,
              padding: '8px 16px',
              fontSize: 12,
              fontWeight: 700,
              cursor: 'pointer',
              animation: 'fadeIn 0.2s ease'
            }}>
              PARIER
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
