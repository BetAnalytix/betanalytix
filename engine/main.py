from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from dotenv import load_dotenv
from team_stats import get_team_stats, get_league_averages
from poisson_model import predict_match
from value_bet import get_odds, simulate_odds, detect_value_bet, kelly_stake, get_real_odds
from telegram_alert import daily_scan, send_value_bet_alert, analyze_mlb_match, analyze_nba_match, analyze_nhl_match
from mlb_stats import get_mlb_today_matches
from nba_stats import get_nba_today_matches
from nhl_stats import get_nhl_today_matches
from scheduler import start_scheduler, stop_scheduler

load_dotenv()

FOOTBALL_DATA_KEY  = os.getenv("FOOTBALL_DATA_API_KEY")
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"

# IDs football-data.org (différents de API-Football)
LEAGUES = {
    39:  {"fd_id": 2021, "name": "Premier League",    "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    140: {"fd_id": 2014, "name": "La Liga",           "flag": "🇪🇸"},
    78:  {"fd_id": 2002, "name": "Bundesliga",        "flag": "🇩🇪"},
    135: {"fd_id": 2019, "name": "Serie A",           "flag": "🇮🇹"},
    61:  {"fd_id": 2015, "name": "Ligue 1",           "flag": "🇫🇷"},
    2:   {"fd_id": 2001, "name": "Champions League",  "flag": "🇪🇺"},
}

app = FastAPI(
    title="BetAnalytix Engine",
    description="Moteur de prédiction — données réelles football-data.org",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()


def fd_headers() -> dict:
    return {"X-Auth-Token": FOOTBALL_DATA_KEY}


async def get_recent_form(team_id: int, fd_league_id: int, season: int, side: str = "home") -> dict:
    stats = await get_team_stats(team_id, fd_league_id, season)
    return stats[f"recent_{side}"]


def apply_recent_form_weight(stats: dict, side: str, recent_stats: dict, weight_recent: float = 0.7) -> dict:
    """
    Applique la pondération 70/30 entre la saison et la forme récente.
    """
    season_avg_gf = stats[side]["goals_scored_avg"]
    season_avg_ga = stats[side]["goals_conceded_avg"]
    
    recent_avg_gf = recent_stats["goals_scored_avg"]
    recent_avg_ga = recent_stats["goals_conceded_avg"]
    
    # Formule : (Saison * 0.3) + (Récent * 0.7)
    weighted_gf = (season_avg_gf * (1 - weight_recent)) + (recent_avg_gf * weight_recent)
    weighted_ga = (season_avg_ga * (1 - weight_recent)) + (recent_avg_ga * weight_recent)
    
    stats[side]["goals_scored_avg"] = round(weighted_gf, 2)
    stats[side]["goals_conceded_avg"] = round(weighted_ga, 2)
    
    return stats


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "engine": "BetAnalytix v0.1",
        "api": "football-data.org v4",
        "api_key_configured": bool(FOOTBALL_DATA_KEY),
        "supported_leagues": {k: v["name"] for k, v in LEAGUES.items()},
    }


@app.get("/standings")
async def get_standings(
    league: int = Query(..., description="ID ligue (ex: 39 = Premier League)"),
    season: int = Query(2024, description="Saison (ex: 2024)"),
):
    if league not in LEAGUES:
        raise HTTPException(
            status_code=400,
            detail=f"Ligue {league} non supportée. IDs valides : {list(LEAGUES.keys())}",
        )

    meta = LEAGUES[league]
    fd_id = meta["fd_id"]

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{FOOTBALL_DATA_BASE}/competitions/{fd_id}/standings",
            headers=fd_headers(),
            params={"season": season},
        )

    if resp.status_code == 403:
        raise HTTPException(status_code=403, detail="Clé API invalide ou plan insuffisant.")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Aucun standing pour league={league} season={season}.")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Erreur football-data.org : {resp.status_code}")

    data = resp.json()

    raw_table = data["standings"][0]["table"]

    standings = []
    for entry in raw_table:
        team = entry["team"]
        all_stats = entry
        standings.append({
            "rank":          entry["position"],
            "team_id":       team["id"],
            "team_name":     team["name"],
            "team_short":    team.get("shortName", team["name"]),
            "team_tla":      team.get("tla", ""),
            "team_crest":    team.get("crest", ""),
            "played":        entry["playedGames"],
            "won":           entry["won"],
            "draw":          entry["draw"],
            "lost":          entry["lost"],
            "goals_for":     entry["goalsFor"],
            "goals_against": entry["goalsAgainst"],
            "goal_diff":     entry["goalDifference"],
            "points":        entry["points"],
            "form":          entry.get("form") or "",
        })

    return {
        "league_id":     league,
        "league_fd_id":  fd_id,
        "league_name":   meta["name"],
        "league_flag":   meta["flag"],
        "season":        season,
        "total_teams":   len(standings),
        "standings":     standings,
    }


@app.get("/team-stats")
async def team_stats(
    team_id:  int = Query(..., description="ID équipe football-data.org (ex: 64 = Liverpool)"),
    league_id: int = Query(..., description="ID ligue (ex: 39 = Premier League)"),
    season: int = Query(2024, description="Saison"),
):
    if league_id not in LEAGUES:
        raise HTTPException(
            status_code=400,
            detail=f"Ligue {league_id} non supportée. IDs valides : {list(LEAGUES.keys())}",
        )

    fd_league_id = LEAGUES[league_id]["fd_id"]

    try:
        result = await get_team_stats(team_id, fd_league_id, season)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return result


@app.get("/predict")
async def predict(
    home_team_id: int = Query(..., description="ID équipe domicile (football-data.org)"),
    away_team_id: int = Query(..., description="ID équipe extérieur (football-data.org)"),
    league_id:    int = Query(..., description="ID ligue (ex: 39 = Premier League)"),
    season:       int = Query(2024, description="Saison"),
):
    if league_id not in LEAGUES:
        raise HTTPException(
            status_code=400,
            detail=f"Ligue {league_id} non supportée. IDs valides : {list(LEAGUES.keys())}",
        )

    fd_league_id = LEAGUES[league_id]["fd_id"]

    # Récupération parallèle : stats des deux équipes + moyennes de ligue
    import asyncio
    try:
        home_stats, away_stats, league_avgs = await asyncio.gather(
            get_team_stats(home_team_id, fd_league_id, season),
            get_team_stats(away_team_id, fd_league_id, season),
            get_league_averages(fd_league_id, season),
        )
        
        # Récupération de la forme récente (3 derniers matchs dom/ext séparément)
        home_recent, away_recent = await asyncio.gather(
            get_recent_form(home_team_id, fd_league_id, season, side="home"),
            get_recent_form(away_team_id, fd_league_id, season, side="away")
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Application de la pondération "Forme Récente" (70% récent, 30% saison)
    home_stats = apply_recent_form_weight(home_stats, "home", home_recent, weight_recent=0.7)
    away_stats = apply_recent_form_weight(away_stats, "away", away_recent, weight_recent=0.7)

    # Modèle de Poisson Dixon-Coles
    proba = predict_match(
        home_stats=home_stats,
        away_stats=away_stats,
        league_avg_home=league_avgs["league_avg_home"],
        league_avg_away=league_avgs["league_avg_away"],
    )

    return {
        "home_team":   home_stats["team_name"],
        "away_team":   away_stats["team_name"],
        "league":      LEAGUES[league_id]["name"],
        "season":      season,
        "model":       "Dixon-Coles / Poisson (Weighted 70/30)",
        "recent_form_impact": "70%",
        "league_averages": {
            "avg_home_goals": league_avgs["league_avg_home"],
            "avg_away_goals": league_avgs["league_avg_away"],
            "source":         league_avgs["source"],
            "matches_used":   league_avgs["total_matches"],
        },
        "home_last_5": home_stats["last_5"],
        "away_last_5": away_stats["last_5"],
        "home_recent_form": home_recent,
        "away_recent_form": away_recent,
        **proba,
    }


@app.get("/scan-today")
async def scan_today(seasons: list[int] = Query(default=[2025, 2024], description="Saisons a scanner (ex: ?seasons=2025&seasons=2024)")):
    leagues = list(LEAGUES.keys())
    return await daily_scan(leagues, seasons)


@app.get("/scan-mlb")
async def scan_mlb(season: int = Query(2024, description="Saison MLB")):
    matches = await get_mlb_today_matches()
    odds = await get_real_odds("baseball_mlb")
    results = []
    for m in matches:
        res = await analyze_mlb_match(m, season, real_odds_list=odds)
        if res["found"]:
            results.append(res)
    
    return {
        "sport": "MLB",
        "matches_analyzed": len(matches),
        "value_bets_found": len(results),
        "results": results
    }


@app.get("/scan-nba")
async def scan_nba(season: int = Query(2023, description="Saison NBA")):
    matches = await get_nba_today_matches()
    odds = await get_real_odds("basketball_nba")
    results = []
    for m in matches:
        res = await analyze_nba_match(m, season, real_odds_list=odds)
        if res["found"]:
            results.append(res)
    
    return {
        "sport": "NBA",
        "matches_analyzed": len(matches),
        "value_bets_found": len(results),
        "results": results
    }


@app.get("/scan-nhl")
async def scan_nhl(season: str = Query("20232024", description="Saison NHL")):
    matches = await get_nhl_today_matches()
    odds = await get_real_odds("icehockey_nhl")
    results = []
    for m in matches:
        res = await analyze_nhl_match(m, season, real_odds_list=odds)
        if res["found"]:
            results.append(res)
    
    return {
        "sport": "NHL",
        "matches_analyzed": len(matches),
        "value_bets_found": len(results),
        "results": results
    }


@app.post("/test-telegram")
async def test_telegram():
    if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID manquant dans .env")

    sample = {
        "league":         "Premier League",
        "league_flag":    "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "home_team":      "Arsenal",
        "away_team":      "Chelsea",
        "match_datetime": "2026-05-05T20:00:00Z",
        "bet_side":       "home",
        "model_prob":     0.612,
        "odds":           1.95,
        "edge":           0.098,
        "kelly_stake":    18.5,
        "score":          75.0,
    }

    ok = await send_value_bet_alert(sample)
    if not ok:
        raise HTTPException(status_code=502, detail="Échec envoi Telegram — vérifiez BOT_TOKEN et CHAT_ID")
    return {"status": "ok", "message": "Message test envoyé sur Telegram"}


@app.get("/analyze")
async def analyze(
    home_team_id: int = Query(..., description="ID équipe domicile (football-data.org)"),
    away_team_id: int = Query(..., description="ID équipe extérieur (football-data.org)"),
    league_id:    int = Query(..., description="ID ligue (ex: 39 = Premier League)"),
    season:       int = Query(2024, description="Saison"),
    fixture_id:   int | None = Query(None, description="ID fixture API-Football (optionnel, pour cotes réelles)"),
):
    if league_id not in LEAGUES:
        raise HTTPException(
            status_code=400,
            detail=f"Ligue {league_id} non supportée. IDs valides : {list(LEAGUES.keys())}",
        )

    fd_league_id = LEAGUES[league_id]["fd_id"]

    import asyncio

    # ── Étape 1 : données réelles en parallèle ──────────────────────────────
    try:
        home_stats, away_stats, league_avgs = await asyncio.gather(
            get_team_stats(home_team_id, fd_league_id, season),
            get_team_stats(away_team_id, fd_league_id, season),
            get_league_averages(fd_league_id, season),
        )

        # Récupération de la forme récente (3 derniers matchs dom/ext séparément)
        home_recent, away_recent = await asyncio.gather(
            get_recent_form(home_team_id, fd_league_id, season, side="home"),
            get_recent_form(away_team_id, fd_league_id, season, side="away")
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Application de la pondération "Forme Récente" (70% récent, 30% saison)
    home_stats = apply_recent_form_weight(home_stats, "home", home_recent, weight_recent=0.7)
    away_stats = apply_recent_form_weight(away_stats, "away", away_recent, weight_recent=0.7)

    # ── Étape 2 : modèle Poisson ────────────────────────────────────────────
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

    # ── Étape 3 : cotes bookmaker ───────────────────────────────────────────
    odds = None
    if fixture_id:
        odds = await get_odds(fixture_id)   # API-Football si clé disponible

    if odds is None:
        odds = simulate_odds(model_probs)   # fallback : marge 7.2%

    # ── Étape 4 : détection value bet ───────────────────────────────────────
    vb = detect_value_bet(model_probs, odds)

    stake = None
    if vb:
        stake = kelly_stake(
            model_prob=vb["model_prob"],
            odds=vb["odds"],
            bankroll=1000.0,
        )

    return {
        "fixture_id":  fixture_id,
        "home_team":   home_stats["team_name"],
        "away_team":   away_stats["team_name"],
        "league":      LEAGUES[league_id]["name"],
        "season":      season,
        "model_info": {
            "type": "Poisson Dixon-Coles",
            "recent_form_weight": "70%",
            "seasonal_weight": "30%"
        },
        "model_probs": {
            "home":  proba["prob_home_win"],
            "draw":  proba["prob_draw"],
            "away":  proba["prob_away_win"],
            "check": proba["check_sum"],
        },
        "lambdas": {
            "home": proba["lambda_home"],
            "away": proba["lambda_away"],
        },
        "predicted_score": proba["predicted_score"],
        "home_last_5":     home_stats["last_5"],
        "away_last_5":     away_stats["last_5"],
        "odds": {
            "home":       odds["home"],
            "draw":       odds["draw"],
            "away":       odds["away"],
            "bookmaker":  odds["bookmaker"],
            "source":     odds["source"],
        },
        "value_bet":   vb,
        "kelly_stake": stake,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
