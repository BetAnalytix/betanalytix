import type { Match } from './football-api'

export type PredictionResult = {
  matchId: number
  probHome: number
  probDraw: number
  probAway: number
  prediction: string
  predictionLabel: string
  confidence: number
  isValueBet: boolean
  valuePct: number | null
  recommendedOdds: number
  recommendedStake?: number // Ajout pour mapper kelly_stake
}

const ENGINE_URL = 'http://localhost:8000/analyze'

export async function generatePrediction(
  match: Match
): Promise<PredictionResult> {
  try {
    const params = new URLSearchParams({
      home_team_id: match.homeTeamId.toString(),
      away_team_id: match.awayTeamId.toString(),
      league_id: match.leagueId.toString(),
      season: '2024',
    })

    const response = await fetch(`${ENGINE_URL}?${params.toString()}`)
    
    if (!response.ok) {
      throw new Error(`Engine API error: ${response.status}`)
    }

    const data = await response.json()

    // Mapping des données provenant du moteur Python (engine/main.py)
    const probHome = Math.round(data.model_probs.home * 100)
    const probDraw = Math.round(data.model_probs.draw * 100)
    const probAway = Math.round(data.model_probs.away * 100)

    const maxProb = Math.max(probHome, probDraw, probAway)
    let prediction = '1'
    let predictionLabel = `Victoire ${match.homeTeam}`
    
    if (probDraw === maxProb) {
      prediction = 'X'
      predictionLabel = 'Match nul'
    } else if (probAway === maxProb) {
      prediction = '2'
      predictionLabel = `Victoire ${match.awayTeam}`
    }

    return {
      matchId: match.id,
      probHome,
      probDraw,
      probAway,
      prediction,
      predictionLabel,
      confidence: Math.round(maxProb), // Utilisation de la proba max comme indice de confiance
      isValueBet: !!data.value_bet,
      valuePct: data.value_bet ? Math.round(data.value_bet.edge * 100) : null,
      recommendedOdds: data.value_bet ? data.odds[data.value_bet.bet] : null,
      recommendedStake: data.kelly_stake || 0
    }
  } catch (error) {
    console.error(`Erreur de prédiction pour le match ${match.id}:`, error)
    // Fallback en cas d'erreur du moteur
    return {
      matchId: match.id,
      probHome: 33,
      probDraw: 33,
      probAway: 34,
      prediction: '?',
      predictionLabel: 'Erreur moteur',
      confidence: 0,
      isValueBet: false,
      valuePct: null,
      recommendedOdds: 1.0,
      recommendedStake: 0
    }
  }
}
