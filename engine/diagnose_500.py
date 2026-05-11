import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_endpoint(name, url):
    print(f"Testing {name}...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url)
            print(f"{name} status: {resp.status_code}")
            if resp.status_code == 500:
                print(f"{name} error: {resp.text}")
            else:
                print(f"{name} response: {resp.text[:200]}...")
    except Exception as e:
        print(f"{name} exception: {e}")

async def main():
    # Start server in background
    # (Since I can't easily see background logs, I'll try to run the logic directly in a script if possible, 
    # but testing the actual endpoint is better to see FastAPI's 500 response)
    
    # Let's try to import and run the logic directly to see the traceback
    from main import app
    from telegram_alert import analyze_nba_match, analyze_nhl_match
    from nba_stats import get_nba_today_matches
    from nhl_stats import get_nhl_today_matches
    from value_bet import get_real_odds

    print("\n--- NBA Diagnostic ---")
    try:
        matches = await get_nba_today_matches()
        print(f"NBA Matches found today: {len(matches)}")
        odds = await get_real_odds("basketball_nba")
        print(f"Real Odds found: {len(odds)}")
        if not matches:
            print("No NBA matches scheduled for today or API returned empty list.")
        for m in matches[:1]:
            print(f"Analyzing first match: {m.get('home_name')} vs {m.get('away_name')}")
            res = await analyze_nba_match(m, season=2023, real_odds_list=odds)
            print(f"NBA Result: {res}")
    except Exception as e:
        print(f"NBA Diagnostic error: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- NHL Diagnostic ---")
    try:
        matches = await get_nhl_today_matches()
        print(f"NHL Matches found today: {len(matches)}")
        odds = await get_real_odds("icehockey_nhl")
        print(f"Real Odds found: {len(odds)}")
        if not matches:
            print("No NHL matches scheduled for today or API returned empty list.")
        for m in matches[:1]:
            print(f"Analyzing first match: {m.get('home_name')} vs {m.get('away_name')}")
            res = await analyze_nhl_match(m, season="20232024", real_odds_list=odds)
            print(f"NHL Result: {res}")
    except Exception as e:
        print(f"NHL Diagnostic error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
