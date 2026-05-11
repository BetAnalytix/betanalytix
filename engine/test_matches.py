import asyncio
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_DATA_KEY  = os.getenv("FOOTBALL_DATA_API_KEY", "")
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"

async def test_fetch():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    print(f"Testing fetch for today: {today}")
    league_id = 2021 # Premier League
    async with httpx.AsyncClient(timeout=15.0) as client:
        url = f"{FOOTBALL_DATA_BASE}/competitions/{league_id}/matches"
        headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        params = {"dateFrom": today, "dateTo": today}
        print(f"URL: {url}")
        print(f"Headers: {headers}")
        print(f"Params: {params}")
        resp = await client.get(url, headers=headers, params=params)
    
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        matches = resp.json().get("matches", [])
        print(f"Found {len(matches)} matches")
        for m in matches:
            print(f"- {m['homeTeam']['name']} vs {m['awayTeam']['name']}")
    else:
        print(f"Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test_fetch())
