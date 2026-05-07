import os
import httpx
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SPORTSDATA_KEY = os.getenv("SPORTSDATA_KEY")
BASE_URL = "https://api.sportsdata.io/v3/tennis/stats/json"

async def get_tennis_today_matches():
    """
    Récupère les matchs ATP et WTA prévus aujourd'hui.
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    # Note: SportsData.io Tennis API a des endpoints spécifiques pour le calendrier
    # On va simuler ou chercher l'endpoint correct. 
    # Habituellement c'est /Schedules/{date}
    
    matches = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        # On tente de récupérer le calendrier du jour
        resp = await client.get(
            f"{BASE_URL}/Schedules/{today}",
            params={"key": SPORTSDATA_KEY}
        )
        if resp.status_code == 200:
            data = resp.json()
            for m in data:
                # Filtrer ATP et WTA
                # On assume que la structure contient 'Tournament' ou 'League'
                # Simplification pour le prototype: on prend tout et on filtrera par les cotes
                matches.append({
                    "match_id": m.get("MatchID"),
                    "home_id": m.get("Player1ID"),
                    "home_name": m.get("Player1Name"),
                    "away_id": m.get("Player2ID"),
                    "away_name": m.get("Player2Name"),
                    "tournament_id": m.get("TournamentID"),
                    "surface": m.get("Surface"), # "Hard", "Clay", "Grass"
                    "match_datetime": m.get("DateTime"),
                    "sport": "Tennis"
                })
    return matches

async def get_player_stats(player_id: int):
    """
    Récupère les stats d'un joueur, incluant son historique récent pour Elo et Fatigue.
    """
    # Endpoint probable: /Player/{playerid} ou /PlayerStatsBySeason/{season}
    # Pour l'Elo, on aurait besoin d'un historique. 
    # Pour le prototype, on simule des stats basées sur les résultats récents si l'API est limitée.
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{BASE_URL}/Player/{player_id}",
            params={"key": SPORTSDATA_KEY}
        )
        if resp.status_code == 200:
            return resp.json()
    return None

def calculate_elo_surface(player_stats: dict, surface: str):
    """
    Calcule ou récupère l'Elo spécifique à la surface.
    Par défaut, on part d'une base de 1500.
    """
    base_elo = 1500
    # Dans une version réelle, on calculerait ça sur l'historique SportsData
    # Ici on simule une pondération via les stats de victoires par surface
    return base_elo

def get_tournament_fatigue(player_id: int, tournament_id: int):
    """
    Calcule la fatigue : nombre de matchs joués dans le tournoi actuel.
    """
    # Simulation
    return 0

def predict_tennis_match(p1_stats: dict, p2_stats: dict, surface: str, h2h: list):
    """
    Modèle de prédiction Elo surface-specific + H2H + Fatigue.
    """
    # Elo de base (simulé ou calculé)
    elo1 = 1500
    elo2 = 1500
    
    # Ajustement Surface (Exemple: +50 si spécialiste)
    # Ajustement H2H
    h2h_bonus = len([m for m in h2h if m['winner_id'] == p1_stats['id']]) * 10
    elo1 += h2h_bonus
    
    # Probabilité Elo standard
    prob1 = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
    prob2 = 1 - prob1
    
    return {
        "prob_home_win": round(prob1, 4),
        "prob_away_win": round(prob2, 4)
    }
