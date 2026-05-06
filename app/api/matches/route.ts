import { NextResponse } from 'next/server'
import { getTodayMatches } from '@/lib/football-api'
import { generatePrediction } from '@/lib/predictions'

export async function GET() {
  try {
    const matches = await getTodayMatches()
    const predictions = matches.map((m, i) =>
      generatePrediction(m, (i % 8) + 1, ((i + 3) % 8) + 1)
    )
    return NextResponse.json({ matches, predictions })
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 500 })
  }
}
