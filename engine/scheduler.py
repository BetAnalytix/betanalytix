import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from telegram_alert import daily_scan

logger = logging.getLogger(__name__)

LEAGUES  = [39, 140, 78, 135, 61, 2]
SEASONS  = [2025, 2024]

scheduler = AsyncIOScheduler()


async def _run_daily_scan():
    logger.info("Scheduler: lancement du scan quotidien...")
    try:
        result = await daily_scan(LEAGUES, SEASONS)
        logger.info(
            "Scan termine -- %d analyses, %d value bet(s), %d alerte(s)",
            result["matches_analyzed"],
            result["value_bets_found"],
            result["alerts_sent"],
        )
    except Exception as e:
        logger.error("Erreur durant le scan: %s", e)


def start_scheduler():
    scheduler.add_job(
        _run_daily_scan,
        CronTrigger(hour=10, minute=0),
        id="daily_scan",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("Scheduler demarre -- scan quotidien a 10h00 heure locale")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
