import asyncio
import logging
import re
from datetime import datetime
from typing import ClassVar

import httpx
import xml.etree.ElementTree as etree

from bs4 import BeautifulSoup
from typing_extensions import override

from scrapers.base_scraper import RequestsOrderScraper, NoAvailableDataError
from scrapers.dto.CustomerDTO import CustomerDTO
from scrapers.dto.OrderDTO import OrderDTO
from logging_config import get_logger

logger = get_logger(__name__)


class FlScraper(RequestsOrderScraper):
    platform: ClassVar[str] = "fl"
    # 5 — "Программирование", other categories can be found in the filter on https://www.fl.ru/projects/
    category: ClassVar[int] = 5
    orders_list_url = "https://www.fl.ru/rss/all.xml?category={category}"
    order_url = "https://www.fl.ru/projects/{order_id}"

    request_delay = 1

    # The RSS title ends with the budget: "Сделать парсер (Бюджет: 5 000 ₽)"
    budget_pattern = re.compile(r"\(Бюджет:\s*([\d\s]+)")

    # Budgets from the RSS feed, filled in get_orders_id and used in get_order
    _prices: ClassVar[dict[int, int | None]] = {}

    @classmethod
    @override
    async def get_orders_id(cls) -> list[int]:
        """
        rss

        Fl allows you to retrieve order listing data in XML format

        :return: list of id
        """
        logger.info("Start to get orders id")

        async with httpx.AsyncClient() as client:
            response = await client.get(cls.orders_list_url.format(category=cls.category), headers=cls.headers)

        logger.log(logging.INFO if response.status_code == 200 else logging.ERROR,
                   f"Status code: {response.status_code}")

        if response.status_code != 200:
            return []

        cls._prices = {}
        for item in etree.fromstring(response.content).findall("channel/item"):
            # Link looks like https://www.fl.ru/projects/5525181/nujen-razrabotchik.html
            order_id = int(item.findtext("guid").split("/")[4])
            budget = cls.budget_pattern.search(item.findtext("title"))
            cls._prices[order_id] = int(re.sub(r"\s", "", budget.group(1))) if budget else None

        logger.info(f"Successfully")
        return list(cls._prices)

    @classmethod
    @override
    async def get_order(cls, order_id: int) -> OrderDTO:
        """
        scram: requests, BS4

        The RSS description is truncated, so the full one is taken from the order page.
        The page is rendered on the server, a browser is not needed.

        :param order_id: int
        :return: OrderDTO
        """
        logger.info("Start to get order info")
        logger.debug(f"Order id: {order_id}")

        await asyncio.sleep(cls.request_delay)
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(cls.order_url.format(order_id=order_id), headers=cls.headers)

        if response.status_code != 200:
            logger.warning(f"Response status code {response.status_code}")
            raise NoAvailableDataError(f"Response status code {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")

        # Full text: "Опубликован 08.09.2026 в 16:22 Последнее изменение: ..."
        publication_timestamp = re.search(r"Опубликован\s+(\d{2}\.\d{2}\.\d{4}) в (\d{2}:\d{2})", soup.get_text(" "))
        logger.debug(f"Publication timestamp: {publication_timestamp.group(0)}")
        publication_timestamp = datetime.strptime(" ".join(publication_timestamp.groups()), "%d.%m.%Y %H:%M")

        order = OrderDTO(
            name=soup.select_one("h1").text.strip(),
            description=soup.select_one(f"#projectp{order_id}").get_text("\n").strip(),
            publication_timestamp=publication_timestamp,

            order_id=order_id,
            platform=cls.platform,
            href=cls.order_url.format(order_id=order_id),

            customer=CustomerDTO(
                name=soup.select_one("#sidebar-content span.font-weight-bold").text.strip(),
                href=None,
                platform=cls.platform
            ),
            price=cls._prices.get(order_id)
        )

        logger.debug(f"Order info: {order}")
        logger.info(f"Successfully")
        return order
