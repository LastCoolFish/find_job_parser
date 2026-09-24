import re
import time
from datetime import datetime, timedelta

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from typing_extensions import override

from scrapers.base_scraper import PlaywrightOrderScraper
from scrapers.dto.CustomerDTO import CustomerDTO
from scrapers.dto.OrderDTO import OrderDTO
from logging_config import get_logger

logger = get_logger(__name__)


class KworkScraper(PlaywrightOrderScraper):
    orders_list_url = "https://kwork.ru/projects?c=11&page={page}"
    order_url = "https://kwork.ru/projects/{order_id}/view"

    @classmethod
    @override
    async def get_orders_id(cls) -> list[int]:
        """
        scram: playwright

        Kwork loads job listing data via JavaScript

        :return: list of id
        """

        logger.info(f"Start to get orders id")

        page: Page = cls._require_page()
        hrefs = []

        start_time = time.perf_counter()
        await page.goto(cls.orders_list_url.format(page=1))

        # Stop loading the page once the necessary elements have loaded
        await page.wait_for_selector(".want-card .wants-card__header-title a", state='attached')
        await page.wait_for_selector(".pagination__item", state='attached')
        await page.evaluate("() => window.stop()")
        end_time = time.perf_counter()

        logger.info(f"The page number 1 loaded in {str(end_time - start_time)}s")

        max_page = int(await (await page.locator(".pagination__item").all())[-2].inner_text())
        want_cards = await page.locator(".want-card .wants-card__header-title a").all()

        # Expanding the vocabulary using new links
        hrefs.extend([await widget.get_attribute("href") for widget in want_cards])

        fails = 0
        for pagen in range(2, max_page + 1):
            start_time = time.perf_counter()
            # If the 30-second timeout limit is exceeded, an error appears
            try:
                await page.goto(cls.orders_list_url.format(page=pagen))
            except PlaywrightTimeoutError:
                fails += 1
                logger.warning(f"The page number {pagen} did not load within 30 seconds.")
                continue

            # Stop loading the page once the necessary elements have loaded
            # This time, we do not expect the navigation module to load.
            await page.wait_for_selector(".want-card .wants-card__header-title a", state='attached')
            await page.evaluate("() => window.stop()")
            end_time = time.perf_counter()

            logger.info(f"The page number {pagen} loaded in {str(end_time - start_time)}s")

            want_cards = await page.locator(".want-card .wants-card__header-title a").all()
            hrefs.extend([await widget.get_attribute("href") for widget in want_cards])

        logger.info(f"Successfully {max_page - fails}/{max_page} pages")
        return list(map(lambda h: int(h.replace("/projects/", "")), hrefs))

    @classmethod
    @override
    async def get_order(cls, order_id: int) -> OrderDTO:
        """
        scram: playwright

        Kwork loads information onto the order page using JavaScript

        :param order_id: order id on site
        :return: order info dict
        """

        def parse_timedelta(text: str) -> timedelta:
            """
            Function for parsing timedelta

            :param text: A string of the form: "Осталось: 19 ч. 7 мин."
            :return: datetime.timedelta
            """

            clean_text = " ".join(text.split())

            # Looks for numbers before "д.", "ч." и "мин."
            days = re.search(r"(\d+)\s*д\.", clean_text)
            hours = re.search(r"(\d+)\s*ч\.", clean_text)
            minutes = re.search(r"(\d+)\s*мин\.", clean_text)

            d = int(days.group(1)) if days else 0
            h = int(hours.group(1)) if hours else 0
            m = int(minutes.group(1)) if minutes else 0

            return timedelta(days=d, hours=h, minutes=m)

        logger.info(f"Start")
        logger.debug(f"order_id: {order_id}, href: {cls.order_url.format(order_id=order_id)}")

        page: Page = cls._require_page()
        start_time = time.perf_counter()
        await page.goto(cls.order_url.format(order_id=order_id))
        end_time = time.perf_counter()

        publication_timestamp = await page.locator("div.want-card__informers-row span").first.inner_text()
        publication_timestamp = datetime.now() + timedelta(days=3) - parse_timedelta(publication_timestamp)


        customer = page.locator("div.mb10.want-payer-statistic.d-flex a").first
        price = await page.locator("div.wants-card__price div.d-inline").inner_text()

        logger.info(f"The page (order id {order_id}) loaded in {str(end_time - start_time)}s")

        order = OrderDTO(
            name=(await page.locator("h1.wants-card__header-title").inner_text()).strip(),
            description=await page.locator("div.breakwords.first-letter").inner_text(),
            publication_timestamp=publication_timestamp,

            order_id=order_id,
            platform="kwork",

            customer=CustomerDTO(
                name=(await customer.inner_text()).strip(),
                href=await customer.get_attribute("href"),
                platform="kwork"
            ),
            price=int(price.replace("₽", "").replace(" ", "").strip()) if price else None,
        )

        logger.debug(f"order: {order}")

        logger.info(f"Successfully")
        return order
