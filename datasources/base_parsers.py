from abc import ABC, abstractmethod

from decouple import config
from playwright.async_api import async_playwright, Page

from datasources.entities.OrderEntity import OrderEntity
from datasources.entities.VacancyEntity import VacancyEntity
from logging_config import get_logger

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

playwright_args = [
    "--blink-settings=imagesEnabled=false",  # отключение изображений
    "--disable-dev-shm-usage",  # оптимизация памяти в контейнерах
    "--disable-blink-features=AutomationControlled",  # убирает из JavaScript флаг navigator.webdriver
    f"--user-agent={headers['User-Agent']}",  # задает строку User-Agent
    "--disable-notifications",  # блокирует push-уведомления от сайтов
    "--disable-background-networking",  # блокирует фоновые сетевые запросы браузера к сервисам Google
    "--window-size=1920,1080"  # задает стартовый размер окна браузера
]

headless = config("HEADLESS", default=True, cast=bool)

logger = get_logger(__name__)


class NoAvailableDataError(Exception):
    pass


class PlaywrightOrderParser(ABC):
    headers = headers
    playwright_args = playwright_args
    headless = headless


    @classmethod
    @abstractmethod
    async def get_orders_id(cls, page: Page) -> list[int]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def get_order(cls, page: Page, order_id: int) -> OrderEntity:
        raise NotImplementedError

    @classmethod
    async def get_orders(cls) -> list[OrderEntity]:
        output_orders = []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=cls.headless, args=cls.playwright_args)
            logger.info("Browser launch successful")
            page = await browser.new_page()

            logger.info(f"Start get orders id")
            ids = await cls.get_orders_id(page)
            logger.debug(f"Orders id: {ids}")

            for order_id in ids:
                try:
                    logger.info(f"Start get order {order_id}")
                    order = await cls.get_order(page, order_id)
                    output_orders.append(order)
                except NotImplementedError as e:
                    logger.error(e)
                    pass
                except NoAvailableDataError as e:
                    logger.error(e)
                    continue
                except Exception as e:
                    logger.error(e)
                    continue

        logger.debug(f"Output orders: {output_orders}")
        return output_orders


class PlaywrightVacancyParser(ABC):
    headers = headers
    playwright_args = playwright_args
    headless = headless

    @classmethod
    @abstractmethod
    async def get_vacancies_id(cls, page: Page) -> list[int]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def get_vacancy(cls, page: Page, vacancy_id: int) -> VacancyEntity:
        raise NotImplementedError

    @classmethod
    async def get_vacancies(cls) -> list[VacancyEntity]:
        output_vacancies = []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=cls.headless, args=cls.playwright_args)
            logger.info("Browser launch successful")
            page = await browser.new_page()

            logger.info(f"Start get vacancy id")
            ids = await cls.get_vacancies_id(page)
            logger.debug(f"Vacancies id: {ids}")

            for vacancy_id in ids:
                try:
                    logger.info(f"Start get vacancy {vacancy_id}")
                    vacancy = await cls.get_vacancy(page, vacancy_id)
                    output_vacancies.append(vacancy)
                except NotImplementedError as e:
                    logger.error(e)
                    pass
                except NoAvailableDataError as e:
                    logger.error(e)
                    continue
                except Exception as e:
                    logger.error(e)
                    continue

        logger.debug(f"Output vacancies: {output_vacancies}")
        return output_vacancies


class RequestsVacancyParser(ABC):
    headers = headers

    @classmethod
    @abstractmethod
    async def get_vacancies_id(cls) -> list[int]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def get_vacancy(cls, vacancy_id: int) -> VacancyEntity:
        raise NotImplementedError

    @classmethod
    async def get_vacancies(cls) -> list[VacancyEntity]:
        output_vacancies = []

        logger.info(f"Start get vacancy id")
        ids = await cls.get_vacancies_id()
        logger.debug(f"Vacancies id: {ids}")

        for vacancy_id in ids:
            try:
                logger.info(f"Start get vacancy {vacancy_id}")
                vacancy = await cls.get_vacancy(vacancy_id)
                output_vacancies.append(vacancy)
            except NotImplementedError as e:
                logger.error(e)
                pass
            except NoAvailableDataError as e:
                logger.error(e)
                continue
            except Exception as e:
                logger.error(e)
                continue

        logger.debug(f"Output vacancies: {output_vacancies}")
        return output_vacancies
