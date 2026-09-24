from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import ClassVar

from decouple import config
from playwright.async_api import async_playwright, Page

from scrapers.dto.OrderDTO import OrderDTO
from scrapers.dto.VacancyDTO import VacancyDTO
from logging_config import get_logger

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

playwright_args = [
    "--blink-settings=imagesEnabled=false",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    f"--user-agent={headers['User-Agent']}",
    "--disable-notifications",
    "--disable-background-networking",
    "--window-size=1920,1080"
]

headless = config("HEADLESS", default=True, cast=bool)

logger = get_logger(__name__)


class NoAvailableDataError(Exception):
    pass


class Scraper(ABC):
    @classmethod
    @abstractmethod
    async def _get_ids(cls) -> list:
        ...

    @classmethod
    @abstractmethod
    async def _get_item(cls, item_id):
        ...

    @classmethod
    async def _get_items(cls) -> list:
        items = []

        ids = await cls._get_ids()
        logger.debug(f"Ids: {ids}")

        for item_id in ids:
            try:
                items.append(await cls._get_item(item_id))
            except Exception as e:
                logger.error(e)
                continue

        logger.debug(f"Items: {items}")
        return items

    @classmethod
    async def collect(cls) -> list:
        return await cls._get_items()


class PlaywrightScraperMixin:
    headers = headers
    playwright_args = playwright_args
    headless = headless

    _page: ClassVar[Page | None] = None

    @classmethod
    def _require_page(cls) -> Page:
        assert cls._page is not None, "_require_page() called outside of _browser_session"
        return cls._page

    @classmethod
    @asynccontextmanager
    async def _browser_session(cls):
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=cls.headless, args=cls.playwright_args)
            logger.info("Browser launch successful")
            cls._page = await browser.new_page()
            try:
                yield
            finally:
                cls._page = None
                await browser.close()


class PlaywrightOrderScraper(Scraper, PlaywrightScraperMixin, ABC):
    @classmethod
    @abstractmethod
    async def get_orders_id(cls) -> list[int]:
        ...

    @classmethod
    @abstractmethod
    async def get_order(cls, order_id: int) -> OrderDTO:
        ...

    @classmethod
    async def _get_ids(cls) -> list[int]:
        logger.info("Start get orders id")
        return await cls.get_orders_id()

    @classmethod
    async def _get_item(cls, item_id: int) -> OrderDTO:
        logger.info(f"Start get order {item_id}")
        return await cls.get_order(item_id)

    @classmethod
    async def collect(cls) -> list[OrderDTO]:
        async with cls._browser_session():
            return await cls._get_items()


class PlaywrightVacancyScraper(Scraper, PlaywrightScraperMixin, ABC):
    @classmethod
    @abstractmethod
    async def get_vacancies_id(cls) -> list[int]:
        ...

    @classmethod
    @abstractmethod
    async def get_vacancy(cls, vacancy_id: int) -> VacancyDTO:
        ...

    @classmethod
    async def _get_ids(cls) -> list[int]:
        logger.info("Start get vacancy id")
        return await cls.get_vacancies_id()

    @classmethod
    async def _get_item(cls, item_id: int) -> VacancyDTO:
        logger.info(f"Start get vacancy {item_id}")
        return await cls.get_vacancy(item_id)

    @classmethod
    async def collect(cls) -> list[VacancyDTO]:
        async with cls._browser_session():
            return await cls._get_items()


class RequestsVacancyScraper(Scraper, ABC):
    headers = headers

    @classmethod
    @abstractmethod
    async def get_vacancies_id(cls) -> list[int]:
        ...

    @classmethod
    @abstractmethod
    async def get_vacancy(cls, vacancy_id: int) -> VacancyDTO:
        ...

    @classmethod
    async def _get_ids(cls) -> list[int]:
        logger.info("Start get vacancy id")
        return await cls.get_vacancies_id()

    @classmethod
    async def _get_item(cls, item_id: int) -> VacancyDTO:
        logger.info(f"Start get vacancy {item_id}")
        return await cls.get_vacancy(item_id)
