import os
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SPORTSDATA_KEY = os.getenv("SPORTSDATA_KEY", "")
BASE_URL = "https://api.sportsdata.io/v3/volleyball/stats/json"

async def get_volleyball_today_matches():
    """
    Récupère les matchs de volleyball prévus aujourd'hui.
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    matches = []
    if not SPORTSDATA_KEY:
        return matches
        
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{BASE_URL}/Schedules/{today}",
            params={"key": SPORTSDATA_KEY}
        )
        if resp.status_code != 200:
            return matches
            
        for m in resp.json():
            matches.append({
                "match_id": m.get("GameId"),
                "home_id": m.get("HomeTeamId"),
                "home_name": m.get("HomeTeamName"),
                "away_id": m.get("AwayTeamId"),
                "away_name": m.get("AwayTeamName"),
                "match_datetime": m.get("DateTime"),
                "sport": "Volleyball"
            })
    return matches

async def get_team_season_stats(team_id: int):
    """
    Récupère les stats de la saison pour une équipe.
    """
    if not SPORTSDATA_KEY or not team_id:
        return None
        
    season = datetime.utcnow().year
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{BASE_URL}/TeamSeasonStats/{season}",
            params={"key": SPORTSDATA_KEY}
        )
        if resp.status_code == 200:
            all_stats = resp.json()
            return next((s for s in all_stats if s.get("TeamId") == team_id), None)
    return None
