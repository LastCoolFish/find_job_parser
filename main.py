import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from collectors.Collector import Collector
from db.engine import create_tables
from repositories.OrdersRepository import OrdersRepository
from repositories.VacancyRepository import VacancyRepository
from scrapers.orders.FlScraper import FlScraper
from scrapers.orders.KworkScraper import KworkScraper
from scrapers.vacancies.HabrScraper import HabrScraper
from scrapers.vacancies.HhScraper import HhScraper
from services.BaseService import BaseService
from services.OrderService import OrderService
from services.VacancyService import VacancyService
from logging_config import get_logger

logger = get_logger(__name__)

SERVICES: tuple[BaseService, ...] = (
    OrderService(Collector([FlScraper, KworkScraper]), OrdersRepository),
    VacancyService(Collector([HabrScraper, HhScraper]), VacancyRepository),
)


async def run_services() -> None:
    for service in SERVICES:
        try:
            await service.run()
        except Exception:
            logger.exception(f"Pipeline {type(service).__name__} failed")


async def main() -> None:
    await create_tables()

    scheduler = AsyncIOScheduler()
    # No explicit next_run_time - APScheduler fires an interval job for the first time
    # immediately on start, then every minutes after that.
    scheduler.add_job(run_services, "interval", minutes=30)
    scheduler.start()

    logger.info("Scheduler started, running every 30 minutes")

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
