import httpx
from datetime import datetime
import asyncio

ESPN_NFL_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

async def get_nfl_today_matches():
    """
    Récupère les matchs NFL via l'API ESPN Scoreboard.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{ESPN_NFL_BASE}/scoreboard")
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        matches = []
        for event in data.get("events", []):
            competition = event.get("competitions", [{}])[0]
            home_team = next(t for t in competition.get("competitors", []) if t.get("homeAway") == "home")
            away_team = next(t for t in competition.get("competitors", []) if t.get("homeAway") == "away")
            
            matches.append({
                "id": event.get("id"),
                "home_id": home_team.get("id"),
                "home_name": home_team.get("team", {}).get("displayName"),
                "away_id": away_team.get("id"),
                "away_name": away_team.get("team", {}).get("displayName"),
                "match_datetime": event.get("date"),
                "sport": "NFL"
            })
    return matches

async def get_nfl_team_stats(team_id: str):
    """
    Récupère les stats d'une équipe NFL (Record pour Elo).
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{ESPN_NFL_BASE}/teams/{team_id}")
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        team_data = data.get("team", {})
        record = team_data.get("record", {}).get("items", [{}])[0].get("summary", "0-0")
        
        # Extraction victoires/défaites simple
        try:
            wins, losses = map(int, record.split('-')[:2])
        except:
            wins, losses = 0, 0
            
        return {
            "id": team_id,
            "name": team_data.get("displayName"),
            "wins": wins,
            "losses": losses,
            "win_pct": wins / (wins + losses) if (wins + losses) > 0 else 0.5
        }
