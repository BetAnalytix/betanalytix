import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Note: balldontlie v1 (nouveau) nécessite une clé API.
# Si l'utilisateur utilise l'ancienne version, le base_url peut varier.
NBA_API_KEY = os.getenv("NBA_API_KEY", "")
NBA_API_BASE = "https://api.balldontlie.io/nba/v1"

def _headers() -> dict:
    return {"Authorization": NBA_API_KEY} if NBA_API_KEY else {}

async def get_nba_teams():
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{NBA_API_BASE}/teams", headers=_headers())
        if resp.status_code != 200:
            return []
        return resp.json().get("data", [])

async def get_nba_team_stats(team_id: int, season: int = 2023):
    """
    Récupère les stats de points (marqués/encaissés) et la forme (5 derniers matchs).
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Stats offensives (base)
        base_resp = await client.get(
            f"{NBA_API_BASE}/team_season_averages/general",
            headers=_headers(),
            params={"season": season, "season_type": "regular", "type": "base", "team_ids[]": [team_id]}
        )
        # Stats défensives (opponent)
        opp_resp = await client.get(
            f"{NBA_API_BASE}/team_season_averages/general",
            headers=_headers(),
            params={"season": season, "season_type": "regular", "type": "opponent", "team_ids[]": [team_id]}
        )
        # 5 derniers matchs pour la forme
        games_resp = await client.get(
            f"{NBA_API_BASE}/games",
            headers=_headers(),
            params={"seasons[]": [season], "team_ids[]": [team_id], "per_page": 10}
        )

    if base_resp.status_code != 200 or opp_resp.status_code != 200 or games_resp.status_code != 200:
        return None

    try:
        base_data = base_resp.json().get("data", [])
        opp_data = opp_resp.json().get("data", [])
        games_data = games_resp.json().get("data", [])
    except Exception:
        return None
    
    if not base_data or not opp_data:
        return None

    stats_base = base_data[0]
    stats_opp = opp_data[0]

    # Forme : 5 derniers matchs
    # Filtrer les matchs terminés et trier par date décroissante
    finished_games = [g for g in games_data if g.get("status") == "Final"]
    finished_games.sort(key=lambda x: x.get("date"), reverse=True)
    
    results = []
    wins_count = 0
    for g in finished_games[:5]:
        home_id = g["home_team"]["id"]
        home_pts = g["home_team_score"]
        visitor_pts = g["visitor_team_score"]
        
        is_home = home_id == team_id
        if is_home:
            won = home_pts > visitor_pts
        else:
            won = visitor_pts > home_pts
            
        results.append("W" if won else "L")
        if won: wins_count += 1

    return {
        "team_id": team_id,
        "avg_pts_scored": stats_base.get("pts", 110.0),
        "avg_pts_allowed": stats_opp.get("pts", 110.0),
        "last_5": results,
        "wins_last_5": wins_count,
        "form_score": wins_count / max(len(results), 1)
    }

async def get_nba_today_matches():
    today = datetime.now().strftime("%Y-%m-%d")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{NBA_API_BASE}/games",
            headers=_headers(),
            params={"dates[]": [today]}
        )
    
    if resp.status_code != 200:
        return []

    try:
        data = resp.json()
    except Exception:
        return []

    matches = []
    for game in data.get("data", []):
        matches.append({
            "id": game.get("id"),
            "home_id": game.get("home_team", {}).get("id"),
            "home_name": game.get("home_team", {}).get("full_name"),
            "away_id": game.get("visitor_team", {}).get("id"),
            "away_name": game.get("visitor_team", {}).get("full_name"),
            "match_datetime": game.get("date")
        })
    return matches

async def get_nba_league_averages(season: int = 2023):
    """
    Récupère la moyenne de points de la ligue.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{NBA_API_BASE}/team_season_averages/general",
            headers=_headers(),
            params={"season": season, "season_type": "regular", "type": "base"}
        )
    
    if resp.status_code != 200:
        return 114.0

    try:
        data = resp.json().get("data", [])
    except Exception:
        return 114.0

    if not data:
        return 114.0 # Moyenne NBA moderne approximative
        
    total_pts = sum(d.get("pts", 0) for d in data)
    return round(total_pts / len(data), 4)
