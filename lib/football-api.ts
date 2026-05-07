const BASE_URL = 'https://api.football-data.org/v4'
const API_KEY = process.env.FOOTBALL_DATA_API_KEY!

const LEAGUE_IDS: Record<string, number> = {
  'Premier League': 2021,
  'La Liga': 2014,
  'Bundesliga': 2002,
  'Serie A': 2019,
  'Ligue 1': 2015,
  'Champions League': 2001,
}

const LEAGUE_FLAGS: Record<string, string> = {
  'Premier League': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  'La Liga': '🇪🇸',
  'Bundesliga': '🇩🇪',
  'Serie A': '🇮🇹',
  'Ligue 1': '🇫🇷',
  'Champions League': '🇪🇺',
}

async function fetchAPI(path: string) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'X-Auth-Token': API_KEY },
    next: { revalidate: 300 },
  })
  if (!res.ok) throw new Error(`Football API error: ${res.status}`)
  return res.json()
}

export type Match = {
  id: number
  league: string
  leagueId: number // ID pour le moteur Python (ex: 39 pour PL)
  leagueFlag: string
  homeTeam: string
  homeTeamId: number
  awayTeam: string
  awayTeamId: number
  matchDate: string
  matchTime: string
  status: string
  homeScore: number | null
  awayScore: number | null
  minute: number | null
}

const REVERSE_LEAGUE_IDS: Record<number, number> = {
  2021: 39,
  2014: 140,
  2002: 78,
  2019: 135,
  2015: 61,
  2001: 2,
}
export async function getTodayMatches(specificDate?: string): Promise<Match[]> {
  const targetDate = specificDate || new Date().toISOString().split('T')[0]
  const results: Match[] = []

  for (const [leagueName, leagueId] of Object.entries(LEAGUE_IDS)) {
    try {
      const data = await fetchAPI(
        `/competitions/${leagueId}/matches?dateFrom=${targetDate}&dateTo=${targetDate}`
      )
      for (const m of data.matches ?? []) {
        results.push({
          id: m.id,
          league: leagueName,
          leagueId: REVERSE_LEAGUE_IDS[leagueId] || 0,
          leagueFlag: LEAGUE_FLAGS[leagueName],
          homeTeam: m.homeTeam.shortName ?? m.homeTeam.name,
          homeTeamId: m.homeTeam.id,
          awayTeam: m.awayTeam.shortName ?? m.awayTeam.name,
          awayTeamId: m.awayTeam.id,
          matchDate: m.utcDate,
          matchTime: new Date(m.utcDate).toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'Europe/Paris',
          }),
          status: m.status,
          homeScore: m.score?.fullTime?.home ?? null,
          awayScore: m.score?.fullTime?.away ?? null,
          minute: m.minute ?? null,
        })
      }
    } catch {
      // skip league on error
    }
  }

  return results
}

export async function getStandings(leagueId: number) {
  try {
    const data = await fetchAPI(`/competitions/${leagueId}/standings`)
    return data.standings?.[0]?.table ?? []
  } catch {
    return []
  }
}

export async function getTeamStats(teamId: number) {
  try {
    const data = await fetchAPI(`/teams/${teamId}/matches?status=FINISHED&limit=10`)
    return data.matches ?? []
  } catch {
    return []
  }
}
