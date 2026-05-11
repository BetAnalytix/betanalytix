import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

async def test_odds_api():
    print(f"Testing Odds API with key: {ODDS_API_KEY[:5]}...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{ODDS_API_BASE}/sports",
            params={"apiKey": ODDS_API_KEY}
        )
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text[:500]}")

if __name__ == "__main__":
    asyncio.run(test_odds_api())
