import asyncio
import os
from telegram_alert import daily_scan
from dotenv import load_dotenv

load_dotenv()

async def debug_scan():
    print("🚀 Démarrage du scan de diagnostic...")
    leagues = [39, 140, 78, 135, 61, 2]
    # On teste avec une seule saison pour aller plus vite
    seasons = [2024]
    
    try:
        # On n'utilise pas wait_for ici pour voir exactement où ça bloque
        print(f"Appel de daily_scan avec leagues={leagues} et seasons={seasons}")
        result = await daily_scan(leagues, seasons)
        print("✅ Scan terminé avec succès !")
        print(f"Résultats : {result}")
    except Exception as e:
        print(f"❌ Erreur pendant le scan : {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_scan())
