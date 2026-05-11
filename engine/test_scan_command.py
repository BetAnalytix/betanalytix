import asyncio
import os
from telegram_alert import daily_scan
from dotenv import load_dotenv

load_dotenv()

async def test_scan():
    leagues = [39, 140, 78, 135, 61, 2]
    seasons = [2024] # On teste avec 2024 car on sait qu'il y a des données
    
    print("🚀 Démarrage du scan de test...")
    try:
        # On limite à une ligue pour aller vite et éviter le 429
        leagues = [39] 
        print(f"Scanning league 39, season 2024...")
        res = await daily_scan(leagues, seasons)
        print(f"✅ Résultat: {res}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scan())
