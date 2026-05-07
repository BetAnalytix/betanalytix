import logging
import httpx
import os
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from telegram_alert import daily_scan

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"

LEAGUES  = [39, 140, 78, 135, 61, 2]
SEASONS  = [2025, 2024]

scheduler = AsyncIOScheduler()

async def get_pending_predictions():
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return []
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/predictions",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            },
            params={
                "status": "eq.pending",
                "date": f"eq.{today}"
            }
        )
        if resp.status_code == 200:
            return resp.json()
    return []

async def update_prediction_status(pred_id: int, status: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.patch(
            f"{SUPABASE_URL}/rest/v1/predictions?id=eq.{pred_id}",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                "Content-Type": "application/json",
            },
            json={"status": status}
        )

async def check_football_result(pred: dict):
    # On cherche le match via football-data.org
    # Note: On n'a pas l'ID football-data dans Supabase, on va filtrer par équipe
    today = datetime.utcnow().strftime("%Y-%m-%d")
    async with httpx.AsyncClient(timeout=10.0) as client:
        # On itère sur les ligues connues pour trouver le match
        for league_id in [2021, 2014, 2002, 2019, 2015, 2001]:
            resp = await client.get(
                f"{FOOTBALL_DATA_BASE}/competitions/{league_id}/matches",
                headers={"X-Auth-Token": FOOTBALL_DATA_KEY},
                params={"dateFrom": today, "dateTo": today}
            )
            if resp.status_code == 200:
                matches = resp.json().get("matches", [])
                for m in matches:
                    if pred["home_team"] in [m["homeTeam"]["name"], m["homeTeam"]["shortName"]] or \
                       pred["away_team"] in [m["awayTeam"]["name"], m["awayTeam"]["shortName"]]:
                        if m["status"] == "FINISHED":
                            winner = m["score"]["winner"] # HOME_TEAM, AWAY_TEAM, DRAW
                            if winner == "HOME_TEAM" and pred["bet"] == "home": return "won"
                            if winner == "AWAY_TEAM" and pred["bet"] == "away": return "won"
                            if winner == "DRAW" and pred["bet"] == "draw": return "won"
                            return "lost"
    return "pending"

async def check_nba_result(pred: dict):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://api.balldontlie.io/v1/games",
            headers={"Authorization": os.getenv("NBA_API_KEY", "")},
            params={"dates[]": [today]}
        )
        if resp.status_code == 200:
            games = resp.json().get("data", [])
            for g in games:
                if pred["home_team"] == g["home_team"]["full_name"]:
                    if g["status"] == "Final":
                        h_score = g["home_score"]
                        a_score = g["visitor_score"]
                        winner = "home" if h_score > a_score else "away"
                        return "won" if pred["bet"] == winner else "lost"
    return "pending"

async def check_mlb_result(pred: dict):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://statsapi.mlb.com/api/v1/schedule",
            params={"sportId": 1, "date": today}
        )
        if resp.status_code == 200:
            data = resp.json()
            for date_info in data.get("dates", []):
                for g in date_info.get("games", []):
                    if pred["home_team"] in g["teams"]["home"]["team"]["name"]:
                        status = g["status"]["abstractGameState"]
                        if status == "Final":
                            h_score = g["teams"]["home"]["score"]
                            a_score = g["teams"]["away"]["score"]
                            winner = "home" if h_score > a_score else "away"
                            return "won" if pred["bet"] == winner else "lost"
    return "pending"

async def check_nhl_result(pred: dict):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"https://api-web.nhle.com/v1/schedule/{today}")
        if resp.status_code == 200:
            data = resp.json()
            for day in data.get("gameWeek", []):
                if day.get("date") == today:
                    for g in day.get("games", []):
                        if pred["home_team"] in g["homeTeam"]["placeName"]["default"]:
                            if g["gameState"] in ["FINAL", "OFF"]:
                                h_score = g["homeTeam"]["score"]
                                a_score = g["awayTeam"]["score"]
                                winner = "home" if h_score > a_score else "away"
                                return "won" if pred["bet"] == winner else "lost"
    return "pending"

async def check_nfl_result(pred: dict):
    today = datetime.utcnow().strftime("%Y%m%d")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
            params={"dates": today}
        )
        if resp.status_code == 200:
            data = resp.json()
            for event in data.get("events", []):
                competition = event.get("competitions", [{}])[0]
                h_team = next((t for t in competition.get("competitors", []) if t.get("homeAway") == "home"), None)
                if h_team and pred["home_team"] in h_team["team"]["displayName"]:
                    if event["status"]["type"]["completed"]:
                        a_team = next((t for t in competition.get("competitors", []) if t.get("homeAway") == "away"), None)
                        h_score = int(h_team["score"])
                        a_score = int(a_team["score"])
                        winner = "home" if h_score > a_score else "away"
                        return "won" if pred["bet"] == winner else "lost"
    return "pending"

async def check_tennis_result(pred: dict):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if not os.getenv("SPORTSDATA_KEY"): return "pending"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"https://api.sportsdata.io/v3/tennis/stats/json/MatchStatsByDate/{today}",
            params={"key": os.getenv("SPORTSDATA_KEY")}
        )
        if resp.status_code == 200:
            for m in resp.json():
                if pred["home_team"] == m["Player1Name"]:
                    if m["Status"] == "Final":
                        winner_id = m["WinnerReceiverId"]
                        winner_side = "home" if winner_id == m["Player1Id"] else "away"
                        return "won" if pred["bet"] == winner_side else "lost"
    return "pending"

async def check_volleyball_result(pred: dict):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if not os.getenv("SPORTSDATA_KEY"): return "pending"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"https://api.sportsdata.io/v3/volleyball/stats/json/MatchStatsByDate/{today}",
            params={"key": os.getenv("SPORTSDATA_KEY")}
        )
        if resp.status_code == 200:
            for m in resp.json():
                if pred["home_team"] == m["HomeTeamName"]:
                    if m["Status"] == "Final":
                        winner_id = m["WinnerId"]
                        winner_side = "home" if winner_id == m["HomeTeamId"] else "away"
                        return "won" if pred["bet"] == winner_side else "lost"
    return "pending"

async def check_daily_results():
    logger.info("Scheduler: vérification des résultats du jour...")
    pending = await get_pending_predictions()
    if not pending:
        logger.info("Aucun pari en attente.")
        return

    results_report = []
    total_staked = 0
    total_returned = 0
    won_count = 0
    date_str = datetime.utcnow().strftime("%Y-%m-%d")

    for pred in pending:
        status = "pending"
        sport = pred["sport"]
        
        if sport == "Football":
            status = await check_football_result(pred)
        elif sport == "NBA":
            status = await check_nba_result(pred)
        elif sport == "MLB":
            status = await check_mlb_result(pred)
        elif sport == "NHL":
            status = await check_nhl_result(pred)
        elif sport == "NFL":
            status = await check_nfl_result(pred)
        elif sport == "Tennis":
            status = await check_tennis_result(pred)
        elif sport == "Volleyball":
            status = await check_volleyball_result(pred)

        if status != "pending":
            await update_prediction_status(pred["id"], status)
            
            stake = pred.get("kelly_stake", 0)
            odds = pred.get("odds", 0)
            total_staked += stake
            
            icon = "✅ GAGNÉ" if status == "won" else "❌ PERDU"
            sport_icon = "⚽"
            if sport == "NBA": sport_icon = "🏀"
            elif sport == "MLB": sport_icon = "⚾"
            elif sport == "NHL": sport_icon = "🏒"
            elif sport == "NFL": sport_icon = "🏈"
            elif sport == "Tennis": sport_icon = "🎾"
            elif sport == "Volleyball": sport_icon = "🏐"
            
            profit_text = ""
            if status == "won":
                won_count += 1
                returned = stake * odds
                total_returned += returned
                profit_text = f"Mise : {stake}$ → Retour : {round(returned, 2)}$\n   Profit : +{round(returned - stake, 2)}$"
            else:
                profit_text = f"Mise : {stake}$ → Perdu : -{stake}$"
            
            results_report.append(
                f"{icon} — {pred['home_team']} vs {pred['away_team']}\n"
                f"   Sport : {sport_icon} {sport}\n"
                f"   {profit_text}"
            )

    if results_report:
        net_profit = total_returned - total_staked
        roi = (net_profit / total_staked * 100) if total_staked > 0 else 0
        
        # Estimation Bankroll (Base 1000 + profit du jour pour le prototype)
        # Idéalement on fetcherait le total_balance réel
        estimated_bankroll = 1000 + net_profit
        
        msg = f"📊 **RÉSULTATS DU JOUR — {date_str}**\n\n"
        msg += "\n\n".join(results_report)
        msg += f"\n\n📈 **Bilan du jour :**\n"
        msg += f"Gagnés : {won_count}/{len(results_report)}\n"
        msg += f"ROI : {round(roi, 1)}%\n"
        msg += f"Profit net : +{round(net_profit, 2)}$\n"
        msg += f"Bankroll estimé : {round(estimated_bankroll, 2)}$"

        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            )

async def _run_daily_scan():
    logger.info("Scheduler: lancement du scan quotidien...")
    try:
        result = await daily_scan(LEAGUES, SEASONS)
        logger.info(
            "Scan termine -- %d analyses, %d value bet(s), %d alerte(s)",
            result["matches_analyzed"],
            result["value_bets_found"],
            result["alerts_sent"],
        )
    except Exception as e:
        logger.error("Erreur durant le scan: %s", e)


def start_scheduler():
    scheduler.add_job(
        _run_daily_scan,
        CronTrigger(hour=10, minute=0),
        id="daily_scan",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        check_daily_results,
        CronTrigger(hour=23, minute=0),
        id="check_results",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("Scheduler demarre -- scan à 10h00, résultats à 23h00")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
