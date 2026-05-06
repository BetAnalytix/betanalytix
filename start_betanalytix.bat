@echo off
TITLE BetAnalytix Launcher
COLOR 0A

echo ==========================================================
echo       LANCEMENT DE L'ECOSYSTEME BETANALYTIX
echo ==========================================================
echo.

:: 1. Lancer le Backend Python (FastAPI)
echo [1/3] Demarrage du Moteur IA (Backend Python)...
start "BetAnalytix - Backend" cmd /k "cd engine && python -m uvicorn main:app --reload --port 8000"

:: 2. Lancer le Frontend Next.js
echo [2/3] Demarrage du Dashboard (Next.js)...
start "BetAnalytix - Frontend" cmd /k "npm run dev"

:: 3. Attendre le chargement (5 secondes)
echo [3/3] Initialisation en cours (attente de 5s)...
timeout /t 5 /nobreak > nul

:: 4. Ouvrir le navigateur
echo.
echo ==========================================================
echo       TOUT EST PRET ! OUVERTURE DU DASHBOARD...
echo ==========================================================
start http://localhost:3000/login

echo.
echo Appuyez sur une touche pour fermer ce lanceur (les serveurs resteront ouverts).
pause > nul
