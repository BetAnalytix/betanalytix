import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def test_telegram():
    print(f"Testing Telegram with Token: {TELEGRAM_BOT_TOKEN[:10]}... and Chat ID: {TELEGRAM_CHAT_ID}")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "🤖 Test BetAnalytix : Les corrections ont été appliquées ! Le scan devrait maintenant fonctionner.",
        "parse_mode": "Markdown"
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json=payload)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
            if resp.status_code == 200:
                print("✅ Message envoyé avec succès !")
            else:
                print("❌ Échec de l'envoi.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_telegram())
