import httpx
import os
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_DATA_KEY  = os.getenv("FOOTBALL_DATA_API_KEY")
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"


def _headers() -> dict:
    return {"X-Auth-Token": FOOTBALL_DATA_KEY}


def _result(match: dict, team_id: int) -> str | None:
    score = match.get("score", {}).get("fullTime", {})
    home = score.get("home")
    away = score.get("away")
    if home is None or away is None:
        return None
    is_home = match["homeTeam"]["id"] == team_id
    if is_home:
        if home > away:  return "W"
        if home < away:  return "L"
        return "D"
    else:
        if away > home:  return "W"
        if away < home:  return "L"
        return "D"


def _goals(match: dict, team_id: int) -> tuple[int, int]:
    """Returns (scored, conceded) for team_id in this match."""
    score = match["score"]["fullTime"]
    h, a = score.get("home") or 0, score.get("away") or 0
    if match["homeTeam"]["id"] == team_id:
        return h, a
    return a, h


def _team_name(matches: list, team_id: int) -> str:
    for m in matches:
        if m["homeTeam"]["id"] == team_id:
            return m["homeTeam"].get("shortName") or m["homeTeam"]["name"]
        if m["awayTeam"]["id"] == team_id:
            return m["awayTeam"].get("shortName") or m["awayTeam"]["name"]
    return f"Team {team_id}"


async def get_team_stats(team_id: int, fd_league_id: int, season: int) -> dict:
    """
    Fetches real match data for a team and computes:
    - Home stats  (played, goals_scored_avg, goals_conceded_avg)
    - Away stats  (played, goals_scored_avg, goals_conceded_avg)
    - Last 5 results as ["W","D","L",...]
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{FOOTBALL_DATA_BASE}/teams/{team_id}/matches",
            headers=_headers(),
            params={
                "status":       "FINISHED",
                "competitions": fd_league_id,
                "season":       season,
            },
        )

    if resp.status_code == 404:
        raise ValueError(f"Équipe {team_id} introuvable.")
    if resp.status_code == 403:
        raise PermissionError("Clé API invalide ou accès refusé.")
    if resp.status_code != 200:
        raise RuntimeError(f"Erreur football-data.org : {resp.status_code} — {resp.text}")

    matches = resp.json().get("matches", [])

    if not matches:
        raise ValueError(
            f"Aucun match terminé trouvé pour team={team_id} "
            f"league={fd_league_id} season={season}."
        )

    # Sort chronologically (oldest → newest)
    matches.sort(key=lambda m: m["utcDate"])

    home_matches = [m for m in matches if m["homeTeam"]["id"] == team_id]
    away_matches = [m for m in matches if m["awayTeam"]["id"] == team_id]

    def avg_goals(match_list: list, team_id: int) -> tuple[float, float]:
        total_scored = total_conceded = 0
        count = 0
        for m in match_list:
            sc, cc = _goals(m, team_id)
            total_scored   += sc
            total_conceded += cc
            count += 1
        if count == 0:
            return 0.0, 0.0
        return round(total_scored / count, 2), round(total_conceded / count, 2)

    home_gf_avg, home_ga_avg = avg_goals(home_matches, team_id)
    away_gf_avg, away_ga_avg = avg_goals(away_matches, team_id)

    # Last 5 results (most recent 5 matches across home + away)
    last_5_raw    = matches[-5:]
    last_5_results = [r for m in last_5_raw if (r := _result(m, team_id)) is not None]

    # Recent Form : 3 derniers matchs dom / 3 derniers matchs ext séparément
    def _recent_stats(match_list: list) -> dict:
        scored = conceded = 0
        for m in match_list:
            sc, cc = _goals(m, team_id)
            scored += sc
            conceded += cc
        count = len(match_list)
        return {
            "played":             count,
            "goals_scored_avg":   round(scored / count, 2) if count > 0 else 0.0,
            "goals_conceded_avg": round(conceded / count, 2) if count > 0 else 0.0,
        }

    return {
        "team_id":   team_id,
        "team_name": _team_name(matches, team_id),
        "season":    season,
        "home": {
            "played":             len(home_matches),
            "goals_scored_avg":   home_gf_avg,
            "goals_conceded_avg": home_ga_avg,
        },
        "away": {
            "played":             len(away_matches),
            "goals_scored_avg":   away_gf_avg,
            "goals_conceded_avg": away_ga_avg,
        },
        "recent_home": _recent_stats(home_matches[-3:]),
        "recent_away": _recent_stats(away_matches[-3:]),
        "last_5": last_5_results,
    }


# Fallback si l'API ne retourne pas les matchs de compétition
_LEAGUE_FALLBACK = {
    2021: {"league_avg_home": 1.53, "league_avg_away": 1.16},  # Premier League
    2014: {"league_avg_home": 1.55, "league_avg_away": 1.10},  # La Liga
    2002: {"league_avg_home": 1.65, "league_avg_away": 1.25},  # Bundesliga
    2019: {"league_avg_home": 1.50, "league_avg_away": 1.05},  # Serie A
    2015: {"league_avg_home": 1.45, "league_avg_away": 1.10},  # Ligue 1
    2001: {"league_avg_home": 1.60, "league_avg_away": 1.15},  # Champions League
}


async def get_league_averages(fd_league_id: int, season: int) -> dict:
    """
    Calcule les moyennes réelles de buts domicile/extérieur depuis
    les matchs terminés de la compétition. Fallback sur des constantes
    historiques si l'endpoint n'est pas accessible.
    """
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(
            f"{FOOTBALL_DATA_BASE}/competitions/{fd_league_id}/matches",
            headers=_headers(),
            params={"season": season, "status": "FINISHED"},
        )

    if resp.status_code != 200:
        fb = _LEAGUE_FALLBACK.get(fd_league_id, {"league_avg_home": 1.50, "league_avg_away": 1.15})
        return {**fb, "total_matches": 0, "source": "fallback"}

    matches = resp.json().get("matches", [])

    if not matches:
        fb = _LEAGUE_FALLBACK.get(fd_league_id, {"league_avg_home": 1.50, "league_avg_away": 1.15})
        return {**fb, "total_matches": 0, "source": "fallback"}

    home_goals = 0
    away_goals = 0
    count = 0

    for m in matches:
        score = m.get("score", {}).get("fullTime", {})
        h = score.get("home")
        a = score.get("away")
        if h is not None and a is not None:
            home_goals += h
            away_goals += a
            count += 1

    if count == 0:
        fb = _LEAGUE_FALLBACK.get(fd_league_id, {"league_avg_home": 1.50, "league_avg_away": 1.15})
        return {**fb, "total_matches": 0, "source": "fallback"}

    return {
        "league_avg_home": round(home_goals / count, 4),
        "league_avg_away": round(away_goals / count, 4),
        "total_matches":   count,
        "source":          "real_data",
    }
