import asyncio
import os
from datetime import datetime

import httpx
from dotenv import load_dotenv

from poisson_model import predict_match
from team_stats import get_league_averages, get_team_stats
from value_bet import detect_value_bet, get_odds, kelly_stake, simulate_odds

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
FOOTBALL_DATA_KEY  = os.getenv("FOOTBALL_DATA_API_KEY", "")
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"

LEAGUES_MAP = {
    39:  {"fd_id": 2021, "name": "Premier League",   "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    140: {"fd_id": 2014, "name": "La Liga",          "flag": "🇪🇸"},
    78:  {"fd_id": 2002, "name": "Bundesliga",       "flag": "🇩🇪"},
    135: {"fd_id": 2019, "name": "Serie A",          "flag": "🇮🇹"},
    61:  {"fd_id": 2015, "name": "Ligue 1",          "flag": "🇫🇷"},
    2:   {"fd_id": 2001, "name": "Champions League", "flag": "🇪🇺"},
}


async def send_value_bet_alert(value_bet_result: dict) -> bool:
    vb = value_bet_result
    bet_team = vb["home_team"] if vb["bet_side"] == "home" else vb["away_team"]

    try:
        dt = datetime.fromisoformat(vb["match_datetime"].replace("Z", "+00:00"))
        date_str = dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        date_str = vb.get("match_datetime", "—")

    text = (
        f"⚽ VALUE BET DÉTECTÉE 🏆 {vb['league_flag']} {vb['league']}\n"
        f"🆚 {vb['home_team']} vs {vb['away_team']}\n"
        f"📅 {date_str} ✅ Pari : Victoire {bet_team}\n"
        f"📊 Probabilité modèle : {round(vb['model_prob'] * 100, 1)}% 💰 Cote : {vb['odds']}\n"
        f"📈 Edge : +{round(vb['edge'] * 100, 1)}%\n"
        f"💵 Mise Kelly : {vb['kelly_stake']}$ / 1000$ ⚠️ Outil personnel — pas un conseil financier"
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
        )
    return resp.status_code == 200


async def _get_today_fixtures(fd_league_id: int) -> list[dict]:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{FOOTBALL_DATA_BASE}/competitions/{fd_league_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_KEY},
            params={"dateFrom": today, "dateTo": today},
        )
    if resp.status_code != 200:
        return []
    return resp.json().get("matches", [])


async def _analyze_match(
    home_id: int,
    away_id: int,
    fd_league_id: int,
    season: int,
    fixture_id: int | None = None,
) -> dict:
    try:
        home_stats, away_stats, league_avgs = await asyncio.gather(
            get_team_stats(home_id, fd_league_id, season),
            get_team_stats(away_id, fd_league_id, season),
            get_league_averages(fd_league_id, season),
        )
    except Exception as e:
        return {"found": False, "home_team": f"id:{home_id}", "away_team": f"id:{away_id}", "reason": f"erreur stats: {e}"}

    home_name = home_stats["team_name"]
    away_name = away_stats["team_name"]

    proba = predict_match(
        home_stats=home_stats,
        away_stats=away_stats,
        league_avg_home=league_avgs["league_avg_home"],
        league_avg_away=league_avgs["league_avg_away"],
    )

    model_probs = {
        "home": proba["prob_home_win"],
        "draw": proba["prob_draw"],
        "away": proba["prob_away_win"],
    }

    odds = None
    if fixture_id:
        odds = await get_odds(fixture_id)
    if odds is None:
        odds = simulate_odds(model_probs)

    vb = detect_value_bet(model_probs, odds)
    if not vb:
        reasons = []
        for side in ("home", "away"):
            cote = odds.get(side)
            prob = model_probs[side]
            if cote is None:
                continue
            edge = prob - (1 / cote)
            if not (1.80 <= cote <= 2.50):
                reasons.append(f"{side}: cote {cote} hors plage [1.80-2.50]")
            elif prob < 0.55:
                reasons.append(f"{side}: prob {round(prob*100,1)}% < 55%")
            elif edge < 0.07:
                reasons.append(f"{side}: edge {round(edge*100,1)}% < 7%")
        return {
            "found":       False,
            "home_team":   home_name,
            "away_team":   away_name,
            "model_probs": model_probs,
            "odds":        {"home": odds["home"], "draw": odds["draw"], "away": odds["away"]},
            "reason":      " | ".join(reasons) if reasons else "aucun candidat valide",
        }

    return {
        "found":       True,
        "home_team":   home_name,
        "away_team":   away_name,
        "bet_side":    vb["bet"],
        "model_prob":  vb["model_prob"],
        "odds":        vb["odds"],
        "edge":        vb["edge"],
        "kelly_stake": kelly_stake(vb["model_prob"], vb["odds"], bankroll=1000.0),
    }


async def daily_scan(leagues: list[int], seasons: list[int]) -> dict:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    matches_analyzed = 0
    candidates: list[dict] = []

    print(f"\n{'='*60}")
    print(f"SCAN DU JOUR - {today} | saisons {seasons}")
    print(f"{'='*60}")

    for league_id in leagues:
        meta = LEAGUES_MAP.get(league_id)
        if not meta:
            continue

        fixtures = await _get_today_fixtures(meta["fd_id"])
        print(f"\n[{meta['name']}] (fd_id={meta['fd_id']}) -> {len(fixtures)} match(s) trouves")

        for fixture in fixtures:
            home_id   = fixture.get("homeTeam", {}).get("id")
            away_id   = fixture.get("awayTeam", {}).get("id")
            home_name = fixture.get("homeTeam", {}).get("name", "?")
            away_name = fixture.get("awayTeam", {}).get("name", "?")
            if not home_id or not away_id:
                continue

            # Essaie les saisons dans l'ordre — s'arrete au premier succes de stats
            for season in seasons:
                matches_analyzed += 1
                print(f"  [MATCH] {home_name} vs {away_name} (s{season}) -> analyse...")
                result = await _analyze_match(home_id, away_id, meta["fd_id"], season)

                if not result["found"]:
                    if "erreur stats" in result["reason"]:
                        print(f"  [SKIP]  s{season} - {result['reason']}")
                        continue  # aucune donnee pour cette saison, essaie la suivante
                    # Stats valides mais pas de value bet
                    print(f"  [NON]   Rejete (s{season}) - {result['reason']}")
                    if "model_probs" in result:
                        p = result["model_probs"]
                        o = result["odds"]
                        print(f"          Probs : dom={round(p['home']*100,1)}%  nul={round(p['draw']*100,1)}%  ext={round(p['away']*100,1)}%")
                        print(f"          Cotes : dom={o['home']}  nul={o['draw']}  ext={o['away']}")
                    break  # analyse valide, pas besoin d'essayer d'autres saisons

                print(f"  [OUI]   VALUE BET : {result['bet_side']} | edge={round(result['edge']*100,1)}% | cote={result['odds']} | Kelly={result['kelly_stake']}$ (s{season})")
                candidate = {k: v for k, v in result.items() if k != "found"}
                candidate.update({
                    "league":         meta["name"],
                    "league_flag":    meta["flag"],
                    "match_datetime": fixture.get("utcDate", today),
                    "season":         season,
                })
                candidates.append(candidate)
                break  # value bet trouve, pas besoin d'essayer d'autres saisons

    candidates.sort(key=lambda x: x["edge"], reverse=True)
    top_3 = candidates[:3]

    alerts_sent = 0
    for vb in top_3:
        if await send_value_bet_alert(vb):
            alerts_sent += 1

    print(f"\n{'='*60}")
    print(f"RESUME : {matches_analyzed} analyses | {len(candidates)} value bet(s) | {alerts_sent} alerte(s) Telegram")
    print(f"{'='*60}\n")

    return {
        "date":             today,
        "matches_analyzed": matches_analyzed,
        "value_bets_found": len(candidates),
        "alerts_sent":      alerts_sent,
        "top_value_bets":   top_3,
    }
