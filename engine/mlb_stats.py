import httpx
from datetime import datetime

MLB_API_BASE = "https://statsapi.mlb.com/api/v1"

async def get_mlb_teams():
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{MLB_API_BASE}/teams?sportId=1")
        return resp.json().get("teams", [])

async def get_mlb_team_stats(team_id: int, season: int = 2024):
    """
    Récupère les stats de runs (scored/allowed) pour une équipe MLB.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Hitting stats (Runs Scored)
        hitting_resp = await client.get(
            f"{MLB_API_BASE}/teams/{team_id}/stats",
            params={"stats": "season", "group": "hitting", "season": season}
        )
        # Pitching stats (Runs Allowed)
        pitching_resp = await client.get(
            f"{MLB_API_BASE}/teams/{team_id}/stats",
            params={"stats": "season", "group": "pitching", "season": season}
        )

    hitting_data = hitting_resp.json().get("stats", [{}])[0].get("splits", [{}])[0].get("stat", {})
    pitching_data = pitching_resp.json().get("stats", [{}])[0].get("splits", [{}])[0].get("stat", {})

    games_played = hitting_data.get("gamesPlayed", 0)
    if games_played == 0:
        return None

    runs_scored = hitting_data.get("runs", 0)
    runs_allowed = pitching_data.get("runs", 0)

    # Forme : 5 derniers matchs
    async with httpx.AsyncClient(timeout=10.0) as client:
        schedule_resp = await client.get(
            f"{MLB_API_BASE}/schedule",
            params={
                "sportId": 1,
                "teamId": team_id,
                "status": "Final",
                "season": season,
                "limit": 5,
                "sortBy": "date",
                "sortOrder": "desc"
            }
        )
    
    matches = schedule_resp.json().get("dates", [])
    results = []
    wins_count = 0
    for date_info in matches:
        for match in date_info.get("games", []):
            teams = match.get("teams", {})
            home = teams.get("home", {})
            away = teams.get("away", {})
            
            is_home = home.get("team", {}).get("id") == team_id
            
            if is_home:
                won = home.get("isWinner", False)
            else:
                won = away.get("isWinner", False)
            
            results.append("W" if won else "L")
            if won:
                wins_count += 1
            if len(results) == 5:
                break
        if len(results) == 5:
            break

    return {
        "team_id": team_id,
        "games_played": games_played,
        "avg_runs_scored": round(runs_scored / games_played, 2),
        "avg_runs_allowed": round(runs_allowed / games_played, 2),
        "last_5": results,
        "wins_last_5": wins_count,
        "form_score": wins_count / max(len(results), 1)
    }

async def get_mlb_today_matches():
    today = datetime.now().strftime("%Y-%m-%d")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{MLB_API_BASE}/schedule",
            params={"sportId": 1, "date": today}
        )
    
    data = resp.json()
    matches = []
    for date_info in data.get("dates", []):
        for game in date_info.get("games", []):
            matches.append({
                "id": game.get("gamePk"),
                "home_id": game.get("teams", {}).get("home", {}).get("team", {}).get("id"),
                "home_name": game.get("teams", {}).get("home", {}).get("team", {}).get("name"),
                "away_id": game.get("teams", {}).get("away", {}).get("team", {}).get("id"),
                "away_name": game.get("teams", {}).get("away", {}).get("team", {}).get("name"),
                "match_datetime": game.get("gameDate")
            })
    return matches

async def get_mlb_league_averages(season: int = 2024):
    """
    Récupère les moyennes de runs pour toute la ligue.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{MLB_API_BASE}/stats",
            params={
                "stats": "season",
                "group": "hitting",
                "season": season,
                "sportId": 1
            }
        )
    
    stats = resp.json().get("stats", [{}])[0].get("splits", [])
    total_runs = 0
    total_games = 0
    for split in stats:
        stat = split.get("stat", {})
        total_runs += stat.get("runs", 0)
        total_games += stat.get("gamesPlayed", 0)
    
    if total_games == 0:
        return 4.5 # Default MLB avg runs per team per game

    # Note: in MLB each game has 2 team-performances.
    # Total runs / Total gamesPlayed (by teams) gives avg runs per team.
    return round(total_runs / total_games, 4)
