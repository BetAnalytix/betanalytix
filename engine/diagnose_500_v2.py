import asyncio
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NBA_API_KEY = os.getenv("NBA_API_KEY", "")
NBA_API_BASE = "https://api.balldontlie.io/nba/v1"
NHL_API_BASE = "https://api-web.nhle.com/v1"

def _headers() -> dict:
    return {"Authorization": NBA_API_KEY} if NBA_API_KEY else {}

async def diagnose_nba():
    print("\n--- NBA Diagnostic ---")
    today = datetime.now().strftime("%Y-%m-%d")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{NBA_API_BASE}/games",
            headers=_headers(),
            params={"dates[]": [today]}
        )
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('Content-Type')}")
        print(f"Body: {resp.text[:500]}")
        try:
            data = resp.json()
            print("JSON valid")
        except Exception as e:
            print(f"JSON error: {e}")

async def diagnose_nhl():
    print("\n--- NHL Diagnostic ---")
    async with httpx.AsyncClient(timeout=10.0) as client:
        standings_resp = await client.get(f"{NHL_API_BASE}/standings/now")
        print(f"Standings Status: {standings_resp.status_code}")
        print(f"Standings Body: {standings_resp.text[:500]}")
        try:
            data = standings_resp.json()
            print("Standings JSON valid")
        except Exception as e:
            print(f"Standings JSON error: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose_nba())
    asyncio.run(diagnose_nhl())
