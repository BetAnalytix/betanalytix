# 🎯 BetAnalytix — Quad-Sport Value Betting Engine

Moteur d'analyse prédictive et de détection de Value Bets couvrant le **Football**, la **NBA**, la **MLB** et la **NHL**.

## 🚀 Fonctionnalités Clés

- **Multi-Sport IA** : 4 modèles statistiques dédiés :
  - ⚽ **Football** : Modèle Poisson Dixon-Coles (1X2).
  - ⚾ **MLB** : Loi de Poisson adaptée aux runs (sans nul).
  - 🏀 **NBA** : Distribution de **Skellam** (optimisée pour les scores élevés).
  - 🏒 **NHL** : Modèle Poisson pour le hockey (redistribution du nul).
- **Power Score (0-100)** : Système de notation propriétaire basé sur l'Edge (40%), la Probabilité (30%), la Forme (20%) et l'Optimisation des Cotes (10%).
- **Intelligence Marché** : Intégration de **The Odds API** pour des cotes en temps réel (NHL, NBA, MLB).
- **Alertes Telegram Unifiées** : Scan global quotidien et envoi du **Top 5** des meilleures opportunités toutes catégories confondues.
- **Filtres de Qualité Stricts** : Seuls les paris avec une Cote [1.80-2.50], une Probabilité >= 55% et un Edge >= 7% sont retenus.

## 🛠 Structure du Projet

- `/app` : Dashboard Next.js (Dashboard Football actuel).
- `/engine` : Backend FastAPI (Le cœur de l'IA).
  - `main.py` : API et Endpoints de scan.
  - `poisson_model.py` : Logique mathématique (Poisson & Skellam).
  - `telegram_alert.py` : Scanner global et système d'alertes.
  - `*_stats.py` : Modules d'extraction de données (MLB, NBA, NHL, Football).

## 📡 Endpoints API Backend

- `GET /scan-today` : Scan complet Quad-Sport + Alerte Telegram.
- `GET /scan-nba` : Analyse spécifique de la journée NBA.
- `GET /scan-nhl` : Analyse spécifique de la journée NHL.
- `GET /scan-mlb` : Analyse spécifique de la journée MLB.
- `GET /analyze` : Analyse détaillée d'un match de Football.

## ⚙️ Configuration (.env)

Ajoutez vos clés dans `engine/.env` :
```env
FOOTBALL_DATA_API_KEY=your_key
NBA_API_KEY=your_balldontlie_key
ODDS_API_KEY=your_the_odds_api_key
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_id
```

## 🏁 Lancement rapide

Utilisez le script `start_betanalytix.bat` à la racine pour lancer tout l'écosystème en un clic.

