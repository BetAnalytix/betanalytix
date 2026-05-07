import numpy as np
from scipy.stats import poisson, skellam

MAX_GOALS = 9  # matrice 9x9 : scores de 0 à 8
MAX_RUNS = 20  # Pour le baseball
MAX_HOCKEY_GOALS = 15 # Pour le hockey


def predict_match(
    home_stats: dict,
    away_stats: dict,
    league_avg_home: float,
    league_avg_away: float,
) -> dict:
    """
    Dixon-Coles simplifié pour le football.
    """
    lambda_home = (
        home_stats["home"]["goals_scored_avg"]
        * away_stats["away"]["goals_conceded_avg"]
        / league_avg_away
    )
    lambda_away = (
        away_stats["away"]["goals_scored_avg"]
        * home_stats["home"]["goals_conceded_avg"]
        / league_avg_home
    )

    goals = np.arange(MAX_GOALS)
    home_pmf = poisson.pmf(goals, lambda_home)
    away_pmf = poisson.pmf(goals, lambda_away)

    matrix = np.outer(home_pmf, away_pmf)
    matrix /= matrix.sum()

    prob_home_win = float(np.tril(matrix, k=-1).sum())
    prob_draw     = float(np.trace(matrix))
    prob_away_win = float(np.triu(matrix, k=1).sum())

    total = prob_home_win + prob_draw + prob_away_win
    prob_home_win /= total
    prob_draw     /= total
    prob_away_win /= total

    best_i, best_j = np.unravel_index(matrix.argmax(), matrix.shape)

    return {
        "lambda_home":    round(float(lambda_home), 4),
        "lambda_away":    round(float(lambda_away), 4),
        "prob_home_win":  round(prob_home_win, 4),
        "prob_draw":      round(prob_draw, 4),
        "prob_away_win":  round(prob_away_win, 4),
        "predicted_score": f"{int(best_i)}-{int(best_j)}",
        "check_sum":      round(prob_home_win + prob_draw + prob_away_win, 10),
    }


def predict_mlb(
    home_stats: dict,
    away_stats: dict,
    league_avg: float,
) -> dict:
    """
    Modèle de Poisson pour le MLB (Baseball).
    """
    lambda_home = (home_stats["avg_runs_scored"] * away_stats["avg_runs_allowed"]) / league_avg
    lambda_away = (away_stats["avg_runs_scored"] * home_stats["avg_runs_allowed"]) / league_avg

    runs = np.arange(MAX_RUNS)
    home_pmf = poisson.pmf(runs, lambda_home)
    away_pmf = poisson.pmf(runs, lambda_away)

    matrix = np.outer(home_pmf, away_pmf)
    matrix /= matrix.sum()

    prob_home_raw = float(np.tril(matrix, k=-1).sum())
    prob_away_raw = float(np.triu(matrix, k=1).sum())
    
    total_no_draw = prob_home_raw + prob_away_raw
    prob_home = prob_home_raw / total_no_draw
    prob_away = prob_away_raw / total_no_draw

    best_i, best_j = np.unravel_index(matrix.argmax(), matrix.shape)

    return {
        "lambda_home": round(float(lambda_home), 4),
        "lambda_away": round(float(lambda_away), 4),
        "prob_home_win": round(prob_home, 4),
        "prob_away_win": round(prob_away, 4),
        "prob_draw": 0.0,
        "predicted_score": f"{int(best_i)}-{int(best_j)}",
    }

def predict_nba(
    home_stats: dict,
    away_stats: dict,
    league_avg: float,
) -> dict:
    """
    Modèle de Poisson pour le NBA (Basketball).
    Utilise la distribution de Skellam.
    """
    lambda_home = (home_stats["avg_pts_scored"] * away_stats["avg_pts_allowed"]) / league_avg
    lambda_away = (away_stats["avg_pts_scored"] * home_stats["avg_pts_allowed"]) / league_avg

    prob_home_raw = 1 - skellam.cdf(0, lambda_home, lambda_away)
    prob_away_raw = skellam.cdf(-1, lambda_home, lambda_away)

    total = prob_home_raw + prob_away_raw
    if total == 0:
        prob_home = 0.5
        prob_away = 0.5
    else:
        prob_home = prob_home_raw / total
        prob_away = prob_away_raw / total

    return {
        "lambda_home": round(float(lambda_home), 2),
        "lambda_away": round(float(lambda_away), 2),
        "prob_home_win": round(prob_home, 4),
        "prob_away_win": round(prob_away, 4),
        "prob_draw": 0.0,
        "predicted_score": f"{round(lambda_home)}-{round(lambda_away)}",
    }

def predict_nhl(
    home_stats: dict,
    away_stats: dict,
    league_avg: float,
) -> dict:
    """
    Modèle de Poisson pour le NHL (Hockey).
    Calcul des lambdas basé sur l'attaque et la défense.
    Redistribution du nul pour un résultat binaire (Vainqueur match).
    """
    lambda_home = (home_stats["avg_goals_scored"] * away_stats["avg_goals_allowed"]) / league_avg
    lambda_away = (away_stats["avg_goals_scored"] * home_stats["avg_goals_allowed"]) / league_avg

    goals = np.arange(MAX_HOCKEY_GOALS)
    home_pmf = poisson.pmf(goals, lambda_home)
    away_pmf = poisson.pmf(goals, lambda_away)

    matrix = np.outer(home_pmf, away_pmf)
    matrix /= matrix.sum()

    prob_home_raw = float(np.tril(matrix, k=-1).sum())
    prob_away_raw = float(np.triu(matrix, k=1).sum())
    
    # Redistribution du nul (Inclus prolongation/tirs au but)
    total_no_draw = prob_home_raw + prob_away_raw
    if total_no_draw == 0:
        prob_home = 0.5
        prob_away = 0.5
    else:
        prob_home = prob_home_raw / total_no_draw
        prob_away = prob_away_raw / total_no_draw

    best_i, best_j = np.unravel_index(matrix.argmax(), matrix.shape)

    return {
        "lambda_home": round(float(lambda_home), 4),
        "lambda_away": round(float(lambda_away), 4),
        "prob_home_win": round(prob_home, 4),
        "prob_away_win": round(prob_away, 4),
        "prob_draw": 0.0,
        "predicted_score": f"{int(best_i)}-{int(best_j)}",
    }

def predict_tennis(
    p1_elo_surface: float,
    p2_elo_surface: float,
    h2h_p1_wins: int,
    h2h_p2_wins: int,
    p1_fatigue: int,
    p2_fatigue: int
) -> dict:
    """
    Modèle Tennis Elo surface-specific + H2H + Fatigue.
    """
    # Ajustement Elo par H2H (Bonus 15 pts par victoire nette d'écart)
    h2h_diff = h2h_p1_wins - h2h_p2_wins
    elo1 = p1_elo_surface + (h2h_diff * 15)
    elo2 = p2_elo_surface - (h2h_diff * 15)
    
    # Ajustement Fatigue (Malus 10 pts par match joué cette semaine)
    elo1 -= (p1_fatigue * 10)
    elo2 -= (p2_fatigue * 10)
    
    # Probabilité Elo standard
    prob1 = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
    prob2 = 1 - prob1
    
    return {
        "prob_home_win": round(prob1, 4),
        "prob_away_win": round(prob2, 4),
        "prob_draw": 0.0,
        "elo_diff": round(elo1 - elo2, 1)
    }

def predict_nfl(
    home_elo: float,
    away_elo: float,
    home_advantage: float = 65.0 # ~2.5 points NFL Elo scale
) -> dict:
    """
    Modèle NFL Elo avec avantage domicile.
    """
    elo_h = home_elo + home_advantage
    elo_a = away_elo
    
    prob_h = 1 / (1 + 10 ** ((elo_a - elo_h) / 400))
    prob_a = 1 - prob_h
    
    return {
        "prob_home_win": round(prob_h, 4),
        "prob_away_win": round(prob_a, 4),
        "prob_draw": 0.0,
        "elo_diff": round(elo_h - elo_a, 1)
    }

def predict_volleyball(
    home_sets_avg: float,
    away_sets_avg: float,
    home_sets_allowed_avg: float,
    away_sets_allowed_avg: float,
    league_avg_sets: float = 1.5 # Moyenne de sets gagnés par match par équipe
) -> dict:
    """
    Modèle Poisson pour le Volleyball (Set-by-Set).
    Prédit la probabilité de victoire finale dans un match au meilleur des 5 sets.
    """
    # Lambdas : espérance de sets gagnés
    lambda_h = (home_sets_avg * away_sets_allowed_avg) / league_avg_sets
    lambda_a = (away_sets_avg * home_sets_allowed_avg) / league_avg_sets
    
    # Probabilité de gagner UN set (simplification via Poisson)
    # Dans un set, probabilité que H marque plus que A
    # Pour le volleyball, on utilise souvent le ratio des lambdas pour la proba d'un set
    prob_set_h = lambda_h / (lambda_h + lambda_a) if (lambda_h + lambda_a) > 0 else 0.5
    prob_set_a = 1 - prob_set_h
    
    # Probabilité match (Best of 5)
    # H gagne si : 3-0, 3-1, 3-2
    p_3_0 = prob_set_h ** 3
    p_3_1 = (prob_set_h ** 3) * prob_set_a * 3 # 3 combinations pour le set perdu avant le 4ème
    p_3_2 = (prob_set_h ** 3) * (prob_set_a ** 2) * 6 # 6 combinations pour 2 sets perdus avant le 5ème
    
    prob_h_win = p_3_0 + p_3_1 + p_3_2
    
    return {
        "prob_home_win": round(float(prob_h_win), 4),
        "prob_away_win": round(float(1 - prob_h_win), 4),
        "prob_draw": 0.0,
        "prob_set_home": round(prob_set_h, 4)
    }
