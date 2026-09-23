import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db.engine import create_tables
from services.order_service import OrderService
from services.vacancy_service import VacancyService
from logging_config import get_logger

logger = get_logger(__name__)

PIPELINES = (OrderService.run, VacancyService.run)


async def run_pipelines() -> None:
    for pipeline in PIPELINES:
        try:
            await pipeline()
        except Exception:
            logger.exception(f"Pipeline {pipeline.__qualname__} failed")


async def main() -> None:
    await create_tables()

    scheduler = AsyncIOScheduler()
    # No explicit next_run_time - APScheduler fires an interval job for the first time
    # immediately on start, then every minutes after that.
    scheduler.add_job(run_pipelines, "interval", minutes=30)
    scheduler.start()

    logger.info("Scheduler started, running every 30 minutes")

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
