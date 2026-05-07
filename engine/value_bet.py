import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_FOOTBALL_KEY  = os.getenv("API_FOOTBALL_KEY", "")
API_FOOTBALL_BASE = "https://v3.football.api-sports.io"

ODDS_API_KEY      = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE     = "https://api.the-odds-api.com/v1"

# Priorité bookmakers : Bet365 (1) > William Hill (2)
TARGET_BOOKMAKERS = [1, 2]
MARKET_NAME = "Match Winner"


# ── Récupération des cotes réelles (API-Football) ───────────────────────────

async def get_odds(fixture_id: int) -> dict | None:
    """
    Appelle API-Football GET /odds pour un fixture donné.
    Retourne None si pas de clé ou si l'API échoue.
    """
    if not API_FOOTBALL_KEY:
        return None

    headers = {"x-apisports-key": API_FOOTBALL_KEY}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{API_FOOTBALL_BASE}/odds",
            headers=headers,
            params={"fixture": fixture_id},
        )

    if resp.status_code != 200:
        return None

    response_data = resp.json().get("response", [])
    if not response_data:
        return None

    bookmakers_data = response_data[0].get("bookmakers", [])

    # Sélection bookmaker par priorité
    chosen = None
    for bm_id in TARGET_BOOKMAKERS:
        for bm in bookmakers_data:
            if bm["id"] == bm_id:
                chosen = bm
                break
        if chosen:
            break

    if not chosen and bookmakers_data:
        chosen = bookmakers_data[0]   # fallback : premier dispo
    if not chosen:
        return None

    # Trouver le marché Match Winner
    market = next((m for m in chosen.get("bets", []) if m["name"] == MARKET_NAME), None)
    if not market:
        return None

    odds_map = {v["value"]: float(v["odd"]) for v in market["values"]}

    home = odds_map.get("Home")
    draw = odds_map.get("Draw")
    away = odds_map.get("Away")

    if not all([home, draw, away]):
        return None

    return {
        "home":       home,
        "draw":       draw,
        "away":       away,
        "bookmaker":  chosen["name"],
        "source":     "api_football",
    }


async def get_real_odds(sport_key: str) -> list[dict]:
    """
    Récupère les cotes pour tous les matchs d'un sport donné via The Odds API.
    """
    if not ODDS_API_KEY:
        return []

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{ODDS_API_BASE}/sports/{sport_key}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal"
            },
        )

    if resp.status_code != 200:
        return []

    return resp.json()


def find_match_odds(odds_list: list[dict], home_team: str, away_team: str) -> dict | None:
    """
    Cherche les cotes d'un match spécifique dans la liste renvoyée par The Odds API.
    """
    # Flou artistique sur les noms d'équipes (parfois différents entre API stats et API cotes)
    for match in odds_list:
        if (home_team.lower() in match["home_team"].lower() or match["home_team"].lower() in home_team.lower()) and \
           (away_team.lower() in match["away_team"].lower() or match["away_team"].lower() in away_team.lower()):
            
            # On prend le premier bookmaker disponible (souvent Bet365 ou William Hill en EU)
            if not match["bookmakers"]: continue
            
            bm = match["bookmakers"][0]
            market = next((m for m in bm["markets"] if m["key"] == "h2h"), None)
            if not market: continue
            
            odds_map = {v["name"]: v["price"] for v in market["outcomes"]}
            
            # Identifier qui est Home et qui est Away dans the-odds-api
            h_odd = odds_map.get(match["home_team"])
            a_odd = odds_map.get(match["away_team"])
            d_odd = odds_map.get("Draw", 1.0) # Fallback 1.0 pour les sports sans nul
            
            return {
                "home": h_odd,
                "draw": d_odd,
                "away": a_odd,
                "bookmaker": bm["title"],
                "source": "the_odds_api"
            }
    return None


# ── Simulation des cotes (fallback sans clé API-Football) ───────────────────

def simulate_odds(model_probs: dict, bookmaker_margin: float = 0.072) -> dict:
    """
    Génère des cotes réalistes depuis les probas du modèle en appliquant
    une marge bookmaker (7.2% = marge typique Bet365 sur PL 1X2).
    """
    ph = model_probs["home"]
    pd = model_probs.get("draw", 0.0)
    pa = model_probs["away"]

    # Distribution de la marge
    total = ph + pd + pa
    ph_adj = ph + bookmaker_margin * (pd + pa) / 2
    pd_adj = pd + bookmaker_margin * (ph + pa) / 2 if pd > 0 else 0
    pa_adj = pa + bookmaker_margin * (ph + pd) / 2

    sum_adj = ph_adj + pd_adj + pa_adj

    return {
        "home":       round(1 / (ph_adj / sum_adj), 2),
        "draw":       round(1 / (pd_adj / sum_adj), 2) if pd > 0 else 0.0,
        "away":       round(1 / (pa_adj / sum_adj), 2),
        "bookmaker":  "simulated_bet365_margin",
        "source":     "simulated",
        "margin_pct": round(bookmaker_margin * 100, 1),
    }


# ── Détection de value bet ───────────────────────────────────────────────────

def detect_value_bet(model_probs: dict, odds: dict) -> dict | None:
    """
    Filtres STRICTS.
    """
    candidates = []

    for side in ("home", "away"):
        model_prob = model_probs[side]
        cote       = odds.get(side)

        if not cote or cote <= 1:
            continue

        implied_prob = round(1 / cote, 6)
        edge         = round(model_prob - implied_prob, 6)

        if not (1.80 <= cote <= 2.50):
            continue
        if model_prob < 0.55:
            continue
        if edge < 0.07:
            continue

        candidates.append({
            "bet":          side,
            "odds":         cote,
            "model_prob":   round(model_prob, 4),
            "implied_prob": round(implied_prob, 4),
            "edge":         round(edge, 4),
            "value":        True,
        })

    if not candidates:
        return None

    return max(candidates, key=lambda x: x["edge"])


# ── Mise recommandée Kelly (quart Kelly) ────────────────────────────────────

def kelly_stake(model_prob: float, odds: float, bankroll: float = 1000.0) -> float:
    b = odds - 1.0
    p = model_prob
    q = 1.0 - p

    f_kelly = (b * p - q) / b

    if f_kelly <= 0:
        return 0.0

    stake = (f_kelly * 0.25) * bankroll
    return round(min(stake, 50.0), 2)
