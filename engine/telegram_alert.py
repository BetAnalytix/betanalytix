import asyncio
import os
from datetime import datetime

import httpx
from dotenv import load_dotenv

from poisson_model import predict_match, predict_mlb, predict_nba, predict_nhl, predict_tennis, predict_nfl, predict_volleyball
from team_stats import get_league_averages, get_team_stats
from mlb_stats import get_mlb_today_matches, get_mlb_team_stats, get_mlb_league_averages
from nba_stats import get_nba_today_matches, get_nba_team_stats, get_nba_league_averages
from nhl_stats import get_nhl_today_matches, get_nhl_team_stats, get_nhl_league_averages
from tennis_stats import (
    get_tennis_today_matches,
    get_player_stats as get_tennis_player_stats, get_h2h,
    get_player_season_stats,
    ranking_to_elo,  form_score_from_season,
    fatigue_from_season
)
from nfl_stats import get_nfl_today_matches, get_nfl_team_stats
from volleyball_stats import get_volleyball_today_matches, get_team_season_stats as get_volley_team_stats
from value_bet import detect_value_bet, get_odds, kelly_stake, simulate_odds, get_real_odds, find_match_odds

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
FOOTBALL_DATA_KEY  = os.getenv("FOOTBALL_DATA_API_KEY", "")
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"

SUPABASE_URL      = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

LEAGUES_MAP = {
    39:  {"fd_id": 2021, "name": "Premier League",   "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    140: {"fd_id": 2014, "name": "La Liga",          "flag": "🇪🇸"},
    78:  {"fd_id": 2002, "name": "Bundesliga",       "flag": "🇩🇪"},
    135: {"fd_id": 2019, "name": "Serie A",          "flag": "🇮🇹"},
    61:  {"fd_id": 2015, "name": "Ligue 1",          "flag": "🇫🇷"},
    2:   {"fd_id": 2001, "name": "Champions League", "flag": "🇪🇺"},
}

def calculate_score(edge: float, prob: float, form: float, odds: float) -> float:
    """
    Calcule un score 0-100 : Edge(40%), Prob(30%), Forme(20%), Cote proche 2.00(10%).
    """
    s_edge = min(edge / 0.15, 1.0) * 40
    s_prob = min(prob / 0.80, 1.0) * 30
    s_form = form * 20
    s_odds = max(0, 1 - abs(odds - 2.0)) * 10
    return round(s_edge + s_prob + s_form + s_odds, 1)

async def save_prediction_to_supabase(vb: dict) -> None:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return

    payload = {
        "date":             datetime.utcnow().strftime("%Y-%m-%d"),
        "sport":            vb.get("sport", "Unknown"),
        "home_team":        vb["home_team"],
        "away_team":        vb["away_team"],
        "bet":              vb["bet_side"],
        "odds":             vb["odds"],
        "model_prob":       vb["model_prob"],
        "edge":             vb["edge"],
        "confidence_score": vb.get("score", 0.0),
        "kelly_stake":      vb["kelly_stake"],
        "status":           "pending",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{SUPABASE_URL}/rest/v1/predictions",
                headers={
                    "apikey":        SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                    "Content-Type":  "application/json",
                    "Prefer":        "return=minimal",
                },
                json=payload,
            )
    except Exception:
        pass


async def send_combined_alert(candidates: list[dict]) -> bool:
    if not candidates:
        return False

    text = "🚀 **TOP 5 VALUE BETS DU JOUR** 🚀\n\n"
    for i, vb in enumerate(candidates[:5]):
        sport_name = vb.get("sport", "Sport")
        sport_icon = "⚽"
        if sport_name == "MLB": sport_icon = "⚾"
        elif sport_name == "NBA": sport_icon = "🏀"
        elif sport_name == "NHL": sport_icon = "🏒"
        elif sport_name == "Tennis": sport_icon = "🎾"
        elif sport_name == "NFL": sport_icon = "🏈"
        elif sport_name == "Volleyball": sport_icon = "🏐"
        
        bet_team = vb["home_team"] if vb["bet_side"] == "home" else vb["away_team"]
        
        text += (
            f"{i+1}. {sport_icon} **[{sport_name}]** {vb['league_flag']} **{vb['home_team']} vs {vb['away_team']}**\n"
            f"   🎯 Pari : {bet_team} | 💰 Cote : {vb['odds']}\n"
            f"   🔥 Score : {vb['score']}/100 | 📈 Edge : +{round(vb['edge'] * 100, 1)}%\n"
            f"   📊 Prob : {round(vb['model_prob'] * 100, 1)}% | 💵 Mise : {vb['kelly_stake']}$\n\n"
        )
    
    text += "⚠️ Outil personnel — pas un conseil financier"

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
        )

    if resp.status_code == 200:
        await asyncio.gather(*[save_prediction_to_supabase(vb) for vb in candidates[:5]])

    return resp.status_code == 200

async def send_value_bet_alert(value_bet_result: dict) -> bool:
    return await send_combined_alert([value_bet_result])

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
        return {"found": False, "reason": f"erreur stats: {e}"}

    home_name = home_stats["team_name"]
    away_name = away_stats["team_name"]

    proba = predict_match(
        home_stats=home_stats,
        away_stats=away_stats,
        league_avg_home=league_avgs["league_avg_home"],
        league_avg_away=league_avgs["league_avg_away"],
    )

    model_probs = {"home": proba["prob_home_win"], "draw": proba["prob_draw"], "away": proba["prob_away_win"]}
    odds = await get_odds(fixture_id) if fixture_id else simulate_odds(model_probs)
    vb = detect_value_bet(model_probs, odds)

    if not vb:
        return {"found": False, "reason": "pas de value bet"}

    if not (1.80 <= vb["odds"] <= 2.50) or vb["model_prob"] < 0.55 or vb["edge"] < 0.07:
        return {"found": False, "reason": "filtres non respectés"}

    h_win_rate = home_stats["last_5"].count("W") / len(home_stats["last_5"]) if home_stats["last_5"] else 0.5
    a_win_rate = away_stats["last_5"].count("W") / len(away_stats["last_5"]) if away_stats["last_5"] else 0.5
    form_score = (h_win_rate + a_win_rate) / 2.0

    score = calculate_score(vb["edge"], vb["model_prob"], form_score, vb["odds"])

    return {
        "found": True, "home_team": home_name, "away_team": away_name,
        "bet_side": vb["bet"], "model_prob": vb["model_prob"], "odds": vb["odds"],
        "edge": vb["edge"], "kelly_stake": kelly_stake(vb["model_prob"], vb["odds"], bankroll=1000.0),
        "score": score, "sport": "Football"
    }

async def analyze_mlb_match(match: dict, season: int = 2024, real_odds_list: list = None) -> dict:
    try:
        home_stats, away_stats, league_avg = await asyncio.gather(
            get_mlb_team_stats(match["home_id"], season),
            get_mlb_team_stats(match["away_id"], season),
            get_mlb_league_averages(season)
        )
    except Exception as e:
        return {"found": False, "reason": f"erreur stats MLB: {e}"}

    if not home_stats or not away_stats:
        return {"found": False, "reason": "stats manquantes"}

    proba = predict_mlb(home_stats, away_stats, league_avg)
    model_probs = {"home": proba["prob_home_win"], "away": proba["prob_away_win"]}
    
    odds = None
    if real_odds_list:
        odds = find_match_odds(real_odds_list, match["home_name"], match["away_name"])
    
    if not odds:
        # Fallback : simulation des cotes si les réelles sont introuvables
        odds = simulate_odds(model_probs)

    vb = detect_value_bet(model_probs, odds)

    if not vb:
        return {"found": False, "reason": "pas de value bet"}

    form_score = (home_stats["form_score"] + away_stats["form_score"]) / 2.0
    score = calculate_score(vb["edge"], vb["model_prob"], form_score, vb["odds"])

    return {
        "found": True, "home_team": match["home_name"], "away_team": match["away_name"],
        "bet_side": vb["bet"], "model_prob": vb["model_prob"], "odds": vb["odds"],
        "edge": vb["edge"], "kelly_stake": kelly_stake(vb["model_prob"], vb["odds"], bankroll=1000.0),
        "score": score, "sport": "MLB", "league_flag": "🇺🇸", "league": "MLB"
    }

async def analyze_nba_match(match: dict, season: int = 2023, real_odds_list: list = None) -> dict:
    try:
        home_stats, away_stats, league_avg = await asyncio.gather(
            get_nba_team_stats(match["home_id"], season),
            get_nba_team_stats(match["away_id"], season),
            get_nba_league_averages(season)
        )
    except Exception as e:
        return {"found": False, "reason": f"erreur stats NBA: {e}"}

    if not home_stats or not away_stats:
        return {"found": False, "reason": "stats manquantes"}

    proba = predict_nba(home_stats, away_stats, league_avg)
    model_probs = {"home": proba["prob_home_win"], "away": proba["prob_away_win"]}
    
    odds = None
    if real_odds_list:
        odds = find_match_odds(real_odds_list, match["home_name"], match["away_name"])
        
    if not odds:
        odds = simulate_odds(model_probs)

    vb = detect_value_bet(model_probs, odds)

    if not vb:
        return {"found": False, "reason": "pas de value bet"}

    form_score = (home_stats["form_score"] + away_stats["form_score"]) / 2.0
    score = calculate_score(vb["edge"], vb["model_prob"], form_score, vb["odds"])

    return {
        "found": True, "home_team": match["home_name"], "away_team": match["away_name"],
        "bet_side": vb["bet"], "model_prob": vb["model_prob"], "odds": vb["odds"],
        "edge": vb["edge"], "kelly_stake": kelly_stake(vb["model_prob"], vb["odds"], bankroll=1000.0),
        "score": score, "sport": "NBA", "league_flag": "🇺🇸", "league": "NBA"
    }

async def analyze_nhl_match(match: dict, season: str = "20232024", real_odds_list: list = None) -> dict:
    try:
        home_stats, away_stats, league_avg = await asyncio.gather(
            get_nhl_team_stats(match["home_abbr"], season),
            get_nhl_team_stats(match["away_abbr"], season),
            get_nhl_league_averages()
        )
    except Exception as e:
        return {"found": False, "reason": f"erreur stats NHL: {e}"}

    if not home_stats or not away_stats:
        return {"found": False, "reason": "stats manquantes"}

    proba = predict_nhl(home_stats, away_stats, league_avg)
    model_probs = {"home": proba["prob_home_win"], "away": proba["prob_away_win"]}
    
    odds = None
    if real_odds_list:
        odds = find_match_odds(real_odds_list, match["home_name"], match["away_name"])
        
    if not odds:
        odds = simulate_odds(model_probs)

    vb = detect_value_bet(model_probs, odds)

    if not vb:
        return {"found": False, "reason": "pas de value bet"}

    form_score = (home_stats["form_score"] + away_stats["form_score"]) / 2.0
    score = calculate_score(vb["edge"], vb["model_prob"], form_score, vb["odds"])

    return {
        "found": True, "home_team": match["home_name"], "away_team": match["away_name"],
        "bet_side": vb["bet"], "model_prob": vb["model_prob"], "odds": vb["odds"],
        "edge": vb["edge"], "kelly_stake": kelly_stake(vb["model_prob"], vb["odds"], bankroll=1000.0),
        "score": score, "sport": "NHL", "league_flag": "🏒", "league": "NHL"
    }

async def analyze_tennis_match(match: dict, real_odds_list: list = None) -> dict:
    try:
        p1_stats, p2_stats, h2h_data, p1_season, p2_season = await asyncio.gather(
            get_tennis_player_stats(match["home_id"]),
            get_tennis_player_stats(match["away_id"]),
            get_h2h(match["home_id"], match["away_id"]),
            get_player_season_stats(match["home_id"]),
            get_player_season_stats(match["away_id"]),
        )

        if not p1_stats or not p2_stats:
            return {"found": False, "reason": "stats joueurs introuvables"}

        p1_elo = ranking_to_elo(p1_stats.get("WorldRanking", 200))
        p2_elo = ranking_to_elo(p2_stats.get("WorldRanking", 200))

        h2h_p1_wins = int((h2h_data or {}).get("Player1Wins", 0) or 0)
        h2h_p2_wins = int((h2h_data or {}).get("Player2Wins", 0) or 0)

        p1_fatigue = fatigue_from_season(p1_season)
        p2_fatigue = fatigue_from_season(p2_season)

        proba = predict_tennis(
            p1_elo_surface=p1_elo,
            p2_elo_surface=p2_elo,
            h2h_p1_wins=h2h_p1_wins,
            h2h_p2_wins=h2h_p2_wins,
            p1_fatigue=p1_fatigue,
            p2_fatigue=p2_fatigue,
        )
        model_probs = {"home": proba["prob_home_win"], "away": proba["prob_away_win"]}

        odds = None
        if real_odds_list:
            odds = find_match_odds(real_odds_list, match["home_name"], match["away_name"])

        if not odds:
            odds = simulate_odds(model_probs)

        vb = detect_value_bet(model_probs, odds)

        if not vb:
            return {"found": False, "reason": "pas de value bet"}

        form_score = (form_score_from_season(p1_season) + form_score_from_season(p2_season)) / 2.0
        score = calculate_score(vb["edge"], vb["model_prob"], form_score, vb["odds"])

        return {
            "found": True, "home_team": match["home_name"], "away_team": match["away_name"],
            "bet_side": vb["bet"], "model_prob": vb["model_prob"], "odds": vb["odds"],
            "edge": vb["edge"], "kelly_stake": kelly_stake(vb["model_prob"], vb["odds"], bankroll=1000.0),
            "score": score, "sport": "Tennis", "league_flag": "🎾", "league": "ATP/WTA"
        }
    except Exception as e:
        return {"found": False, "reason": f"erreur stats Tennis: {e}"}

async def analyze_nfl_match(match: dict, real_odds_list: list = None) -> dict:
    try:
        home_stats, away_stats = await asyncio.gather(
            get_nfl_team_stats(match["home_id"]),
            get_nfl_team_stats(match["away_id"])
        )
        
        if not home_stats or not away_stats:
            return {"found": False, "reason": "stats NFL manquantes"}
            
        # Elo NFL basique basé sur le win% (simulé pour le prototype: win% * 400 + 1300)
        home_elo = home_stats["win_pct"] * 400 + 1300
        away_elo = away_stats["win_pct"] * 400 + 1300
        
        proba = predict_nfl(home_elo, away_elo)
        model_probs = {"home": proba["prob_home_win"], "away": proba["prob_away_win"]}
        
        odds = None
        if real_odds_list:
            odds = find_match_odds(real_odds_list, match["home_name"], match["away_name"])
            
        if not odds:
            odds = simulate_odds(model_probs)

        vb = detect_value_bet(model_probs, odds)

        if not vb:
            return {"found": False, "reason": "pas de value bet NFL"}

        form_score = (home_stats["win_pct"] + away_stats["win_pct"]) / 2.0
        score = calculate_score(vb["edge"], vb["model_prob"], form_score, vb["odds"])

        return {
            "found": True, "home_team": match["home_name"], "away_team": match["away_name"],
            "bet_side": vb["bet"], "model_prob": vb["model_prob"], "odds": vb["odds"],
            "edge": vb["edge"], "kelly_stake": kelly_stake(vb["model_prob"], vb["odds"], bankroll=1000.0),
            "score": score, "sport": "NFL", "league_flag": "🇺🇸", "league": "NFL"
        }
    except Exception as e:
        return {"found": False, "reason": f"erreur stats NFL: {e}"}

async def analyze_volleyball_match(match: dict, real_odds_list: list = None) -> dict:
    try:
        home_stats, away_stats = await asyncio.gather(
            get_volley_team_stats(match["home_id"]),
            get_volley_team_stats(match["away_id"])
        )
        
        if not home_stats or not away_stats:
            return {"found": False, "reason": "stats Volleyball manquantes"}
            
        # Extraction des sets gagnés/perdus (dépend du schéma SportsData)
        # On assume: SetsWon, SetsLost, Games (nombre de matchs)
        h_games = max(home_stats.get("Games", 1), 1)
        a_games = max(away_stats.get("Games", 1), 1)
        
        proba = predict_volleyball(
            home_sets_avg = home_stats.get("SetsWon", 0) / h_games,
            away_sets_avg = away_stats.get("SetsWon", 0) / a_games,
            home_sets_allowed_avg = home_stats.get("SetsLost", 0) / h_games,
            away_sets_allowed_avg = away_stats.get("SetsLost", 0) / a_games
        )
        model_probs = {"home": proba["prob_home_win"], "away": proba["prob_away_win"]}
        
        odds = None
        if real_odds_list:
            odds = find_match_odds(real_odds_list, match["home_name"], match["away_name"])
            
        if not odds:
            odds = simulate_odds(model_probs)

        vb = detect_value_bet(model_probs, odds)

        if not vb:
            return {"found": False, "reason": "pas de value bet Volleyball"}

        # Form score basé sur le win rate de la saison
        h_win_rate = home_stats.get("Wins", 0) / h_games
        a_win_rate = away_stats.get("Wins", 0) / a_games
        form_score = (h_win_rate + a_win_rate) / 2.0
        
        score = calculate_score(vb["edge"], vb["model_prob"], form_score, vb["odds"])

        return {
            "found": True, "home_team": match["home_name"], "away_team": match["away_name"],
            "bet_side": vb["bet"], "model_prob": vb["model_prob"], "odds": vb["odds"],
            "edge": vb["edge"], "kelly_stake": kelly_stake(vb["model_prob"], vb["odds"], bankroll=1000.0),
            "score": score, "sport": "Volleyball", "league_flag": "🏐", "league": "World League"
        }
    except Exception as e:
        return {"found": False, "reason": f"erreur stats Volleyball: {e}"}

async def daily_scan(leagues: list[int], seasons: list[int]) -> dict:
    candidates: list[dict] = []
    matches_analyzed = 0
    
    # --- PRÉ-CHARGEMENT DES COTES RÉELLES ---
    mlb_odds, nba_odds, nhl_odds, atp_odds, wta_odds, nfl_odds, volley_odds = await asyncio.gather(
        get_real_odds("baseball_mlb"),
        get_real_odds("basketball_nba"),
        get_real_odds("icehockey_nhl"),
        get_real_odds("tennis_atp"),
        get_real_odds("tennis_wta"),
        get_real_odds("americanfootball_nfl"),
        get_real_odds("volleyball_wovb")
    )
    
    tennis_odds = atp_odds + wta_odds
    
    # --- SCAN FOOTBALL ---
    for league_id in leagues:
        meta = LEAGUES_MAP.get(league_id)
        if not meta: continue
        fixtures = await _get_today_fixtures(meta["fd_id"])
        for f in fixtures:
            matches_analyzed += 1
            for s in seasons:
                res = await _analyze_match(f.get("homeTeam", {}).get("id"), f.get("awayTeam", {}).get("id"), meta["fd_id"], s)
                if res["found"]:
                    res.update({"league": meta["name"], "league_flag": meta["flag"], "match_datetime": f["utcDate"]})
                    candidates.append(res)
                    break

    # --- SCAN MLB ---
    mlb_matches = await get_mlb_today_matches()
    for m in mlb_matches:
        matches_analyzed += 1
        res = await analyze_mlb_match(m, real_odds_list=mlb_odds)
        if res["found"]:
            res.update({"match_datetime": m["match_datetime"]})
            candidates.append(res)

    # --- SCAN NBA ---
    nba_matches = await get_nba_today_matches()
    for m in nba_matches:
        matches_analyzed += 1
        res = await analyze_nba_match(m, real_odds_list=nba_odds)
        if res["found"]:
            res.update({"match_datetime": m["match_datetime"]})
            candidates.append(res)

    # --- SCAN NHL ---
    nhl_matches = await get_nhl_today_matches()
    for m in nhl_matches:
        matches_analyzed += 1
        res = await analyze_nhl_match(m, real_odds_list=nhl_odds)
        if res["found"]:
            res.update({"match_datetime": m["match_datetime"]})
            candidates.append(res)

    # --- SCAN TENNIS ---
    tennis_matches = await get_tennis_today_matches()
    for m in tennis_matches:
        matches_analyzed += 1
        res = await analyze_tennis_match(m, real_odds_list=tennis_odds)
        if res["found"]:
            res.update({"match_datetime": m["match_datetime"]})
            candidates.append(res)

    # --- SCAN NFL ---
    nfl_matches = await get_nfl_today_matches()
    for m in nfl_matches:
        matches_analyzed += 1
        res = await analyze_nfl_match(m, real_odds_list=nfl_odds)
        if res["found"]:
            res.update({"match_datetime": m["match_datetime"]})
            candidates.append(res)

    # --- SCAN VOLLEYBALL ---
    volley_matches = await get_volleyball_today_matches()
    for m in volley_matches:
        matches_analyzed += 1
        res = await analyze_volleyball_match(m, real_odds_list=volley_odds)
        if res["found"]:
            res.update({"match_datetime": m["match_datetime"]})
            candidates.append(res)

    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    top_5 = candidates[:5]
    alerts_sent = 1 if top_5 else 0
    if top_5:
        await send_combined_alert(top_5)

    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "matches_analyzed": matches_analyzed,
        "value_bets_found": len(candidates),
        "alerts_sent": alerts_sent,
        "top_value_bets": top_5
    }
