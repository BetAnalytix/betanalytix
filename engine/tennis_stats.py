import os
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SPORTSDATA_KEY = os.getenv("SPORTSDATA_KEY", "")
BASE_URL = "https://api.sportsdata.io/v3/tennis/stats/json"


def ranking_to_elo(ranking: int) -> float:
    """ATP/WTA ranking → Elo proxy. #1 ≈ 2400, #100 ≈ 1700, #500 ≈ 1350."""
    if not ranking or ranking <= 0:
        ranking = 200
    return max(1000.0, round(2400 - (ranking - 1) * 7.0, 1))


def form_score_from_season(stats: dict | None) -> float:
    """Win rate from season stats as form proxy (0.0–1.0)."""
    if not stats:
        return 0.5
    wins   = int(stats.get("Wins",   0) or 0)
    losses = int(stats.get("Losses", 0) or 0)
    total  = wins + losses
    return round(wins / total, 4) if total > 0 else 0.5


def fatigue_from_season(stats: dict | None) -> int:
    """Matches played in current tournament as fatigue proxy."""
    if not stats:
        return 1
    return int(stats.get("TournamentMatchesPlayed", 0) or 0)


async def get_tennis_today_matches() -> list[dict]:
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
                "match_id":       m.get("MatchID"),
                "home_id":        m.get("Player1ID"),
                "home_name":      m.get("Player1Name"),
                "away_id":        m.get("Player2ID"),
                "away_name":      m.get("Player2Name"),
                "tournament_id":  m.get("TournamentID"),
                "surface":        m.get("Surface"),
                "match_datetime": m.get("DateTime"),
                "sport":          "Tennis",
            })
    return matches


async def get_player_stats(player_id: int) -> dict | None:
    """Player profile — includes WorldRanking."""
    if not SPORTSDATA_KEY or not player_id:
        return None
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{BASE_URL}/Player/{player_id}",
            params={"key": SPORTSDATA_KEY}
        )
        if resp.status_code == 200:
            return resp.json()
    return None


async def get_h2h(player1_id: int, player2_id: int) -> dict | None:
    """Head-to-head record between two players."""
    if not SPORTSDATA_KEY or not player1_id or not player2_id:
        return None
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{BASE_URL}/H2H/{player1_id}/{player2_id}",
            params={"key": SPORTSDATA_KEY}
        )
        if resp.status_code == 200:
            return resp.json()
    return None


async def get_player_season_stats(player_id: int) -> dict | None:
    """Season stats — used for win rate (form) and matches played (fatigue)."""
    if not SPORTSDATA_KEY or not player_id:
        return None
    season = datetime.utcnow().year
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{BASE_URL}/PlayerSeasonStats/{player_id}",
            params={"key": SPORTSDATA_KEY, "season": season}
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                return data[0] if data else None
            return data if isinstance(data, dict) else None
    return None
