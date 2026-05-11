import httpx
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NHL_API_BASE = "https://api-web.nhle.com/v1"

async def get_nhl_team_stats(team_abbr: str, season: str = "20232024"):
    """
    Récupère les stats de buts (marqués/encaissés) et la forme (5 derniers matchs).
    """
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        # Stats globales de l'équipe
        stats_resp = await client.get(f"{NHL_API_BASE}/club-stats/{team_abbr}/{season}/2") # 2 = Regular Season
        # Calendrier pour la forme
        schedule_resp = await client.get(f"{NHL_API_BASE}/club-schedule-season/{team_abbr}/{season}")

    if stats_resp.status_code != 200 or schedule_resp.status_code != 200:
        return None

    stats_data = stats_resp.json()
    # Dans l'API NHL v1, club-stats retourne une liste de joueurs. 
    # Pour les stats d'équipe, on peut utiliser le scoreboard ou standings, 
    # ou agréger les stats joueurs, mais standings est plus simple pour les buts d'équipe.
    
    # Correction : Utilisation de standings pour les stats d'équipe
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        standings_resp = await client.get(f"{NHL_API_BASE}/standings/now")
    
    if standings_resp.status_code != 200:
        return None

    standings_data = standings_resp.json().get("standings", [])
    team_standing = next((s for s in standings_data if s["teamAbbrev"]["default"] == team_abbr), None)
    
    if not team_standing:
        return None

    games_played = team_standing.get("gamesPlayed", 0)
    if games_played == 0: return None

    avg_goals_scored = team_standing.get("goalFor", 0) / games_played
    avg_goals_allowed = team_standing.get("goalAgainst", 0) / games_played

    # Forme : 5 derniers matchs
    schedule_data = schedule_resp.json().get("games", [])
    finished_games = [g for g in schedule_data if g.get("gameOutcome", {}).get("lastPeriodType") in ["REG", "OT", "SO"]]
    # Trier par date décroissante
    finished_games.sort(key=lambda x: x.get("gameDate"), reverse=True)
    
    results = []
    wins_count = 0
    for g in finished_games[:5]:
        # Déterminer si l'équipe a gagné
        # Dans club-schedule, on a homeTeam et awayTeam
        is_home = g["homeTeam"]["abbrev"] == team_abbr
        home_score = g["homeTeam"]["score"]
        away_score = g["awayTeam"]["score"]
        
        won = False
        if is_home:
            won = home_score > away_score
        else:
            won = away_score > home_score
            
        results.append("W" if won else "L")
        if won: wins_count += 1

    return {
        "team_abbr": team_abbr,
        "avg_goals_scored": round(avg_goals_scored, 2),
        "avg_goals_allowed": round(avg_goals_allowed, 2),
        "last_5": results,
        "wins_last_5": wins_count,
        "form_score": wins_count / 5.0
    }

async def get_nhl_today_matches():
    today = datetime.now().strftime("%Y-%m-%d")
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.get(f"{NHL_API_BASE}/schedule/{today}")
    
    if resp.status_code != 200:
        return []

    try:
        data = resp.json()
    except Exception:
        return []
        
    matches = []
    # L'API schedule retourne une liste de "gameWeek"
    for day in data.get("gameWeek", []):
        if day.get("date") == today:
            for game in day.get("games", []):
                matches.append({
                    "id": game.get("id"),
                    "home_abbr": game.get("homeTeam", {}).get("abbrev"),
                    "home_name": game.get("homeTeam", {}).get("placeName", {}).get("default"),
                    "away_abbr": game.get("awayTeam", {}).get("abbrev"),
                    "away_name": game.get("awayTeam", {}).get("placeName", {}).get("default"),
                    "match_datetime": game.get("startTimeUTC")
                })
    return matches

async def get_nhl_league_averages():
    """
    Récupère la moyenne de buts de la ligue via les standings.
    """
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.get(f"{NHL_API_BASE}/standings/now")
    
    if resp.status_code != 200:
        return 3.1 # Moyenne NHL historique approx
        
    try:
        standings = resp.json().get("standings", [])
    except Exception:
        return 3.1

    if not standings: return 3.1

    total_goals = sum(s.get("goalFor", 0) for s in standings)
    total_games = sum(s.get("gamesPlayed", 0) for s in standings)
    
    if total_games == 0: return 3.1
    
    return round(total_goals / total_games, 4)
