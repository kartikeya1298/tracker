import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.pipeline import run_pipeline

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scheduled_run():
    logger.info("Starting scheduled scrape run")
    try:
        run = await run_pipeline()
        logger.info(
            "Scrape run complete: %s companies, %s jobs found, %s new",
            run.companies_scraped,
            run.jobs_found,
            run.new_jobs,
        )
    except Exception:
        logger.exception("Scheduled scrape run failed")


def start_scheduler():
    settings = get_settings()
    scheduler.add_job(
        scheduled_run,
        trigger=IntervalTrigger(minutes=settings.scrape_interval_minutes),
        id="career_monitor",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("Scheduler started: monitoring every %s minutes", settings.scrape_interval_minutes)


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
