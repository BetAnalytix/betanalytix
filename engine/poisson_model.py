import numpy as np
from scipy.stats import poisson

MAX_GOALS = 9  # matrice 9x9 : scores de 0 à 8


def predict_match(
    home_stats: dict,
    away_stats: dict,
    league_avg_home: float,
    league_avg_away: float,
) -> dict:
    """
    Dixon-Coles simplifié :
      lambda_home = attack_home * defense_away / league_avg_away
      lambda_away = attack_away * defense_home / league_avg_home

    Retourne probabilités 1X2 + score le plus probable.
    Les 3 probas somment exactement à 1.0.
    """

    # ── Lambdas (buts attendus) ──────────────────────────────────────────────
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

    # ── Distribution de Poisson pour 0..8 buts ──────────────────────────────
    goals = np.arange(MAX_GOALS)                          # [0, 1, ..., 8]
    home_pmf = poisson.pmf(goals, lambda_home)            # P(home = k)
    away_pmf = poisson.pmf(goals, lambda_away)            # P(away = k)

    # Matrice de scores : matrix[i, j] = P(home=i, away=j)
    matrix = np.outer(home_pmf, away_pmf)

    # Normalisation : compense la troncature à 8 buts
    matrix /= matrix.sum()

    # ── Probabilités 1X2 ────────────────────────────────────────────────────
    # Victoire domicile : i > j  → triangle inférieur strict
    prob_home_win = float(np.tril(matrix, k=-1).sum())
    # Nul : i == j  → trace
    prob_draw     = float(np.trace(matrix))
    # Victoire extérieur : j > i  → triangle supérieur strict
    prob_away_win = float(np.triu(matrix, k=1).sum())

    # Garantie mathématique : somme = 1.0 exact (redistribution flottante)
    total = prob_home_win + prob_draw + prob_away_win
    prob_home_win /= total
    prob_draw     /= total
    prob_away_win /= total

    # ── Score le plus probable ───────────────────────────────────────────────
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
