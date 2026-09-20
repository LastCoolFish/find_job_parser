import logging
from datetime import datetime
import httpx


import requests

from playwright.async_api import Page
from typing_extensions import override

import xml.etree.ElementTree as etree

from datasources.base_parsers import PlaywrightOrderParser
from datasources.entities.customer_entity import CustomerEntity
from datasources.entities.order_entity import OrderEntity

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(f"logs/{__name__}.log", mode='w', encoding="utf-8")
formatter = logging.Formatter("%(asctime)s | %(name)s %(funcName)s %(lineno)d | %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class FlParser(PlaywrightOrderParser):
    orders_list_url = "https://www.fl.ru/rss/?category=5"
    order_url = "https://www.fl.ru/projects/{order_id}"

    @classmethod
    @override
    async def get_orders_id(cls, page: Page) -> list[int]:
        """
        rss

        Fl allows you to retrieve order listing data in XML format

        :param page: playwright.sync_api Page
        :return: list of id
        """
        logger.info("Start to get orders id")


        async with httpx.AsyncClient() as client:
            response = await client.get(cls.orders_list_url, headers=cls.headers)

        logger.log(logging.INFO if response.status_code == 200 else logging.ERROR,
                   f"Status code: {response.status_code}")

        if response.status_code == 200:
            data = etree.fromstring(response.content).findall("channel/item/guid")
            urls = set(map(lambda xml: xml.text, data))
            # How to extract the order id from the link
            cleaner = lambda text: int(text.split("/")[4])

            logger.info(f"Successfully")
            return list(map(cleaner, urls))
        return []

    @classmethod
    @override
    async def get_order(cls, page: Page, order_id: int) -> OrderEntity:
        """
        scram: playwright

        Fl loads information onto the order page using JavaScript

        :param page: playwright.sync_api Page
        :param order_id: int
        :return: dict["name": str, "description": str, "customers": dict["name": str, "href": None], "price": int, "link": str]
        """
        logger.info("Start to get order info")
        logger.debug(f"Order id: {order_id}")
        await page.goto(cls.order_url.format(order_id=order_id))

        price = page.locator("span").filter(has=page.locator("fl-rub"))

        publication_timestamp = await page.get_by_text("Опубликован ").inner_text()
        # Full text: "Опубликован 08.09.2026 в 16:22 Последнее изменение: 16.09.2026 в 08:52", so it gets truncated to 31 characters.
        logger.debug(f"Publication timestamp: {publication_timestamp[:30]}")
        publication_timestamp = datetime.strptime(publication_timestamp[:30], "Опубликован %d.%m.%Y в %H:%M")


        order = OrderEntity(
            name=(await page.locator("h1").inner_text()).strip(),
            description=await page.locator(f"#projectp{order_id}").inner_text(),
            publication_timestamp=publication_timestamp,

            order_id=order_id,
            platform="fl",

            customer=CustomerEntity(
                name=await page.locator("#sidebar-content span.font-weight-bold").inner_text(),
                href=None
            ),
            price=int((await price.inner_text()).replace("₽", "").strip()) if await price.count() > 0 else None
        )

        logger.debug(f"Order info: {order}")
        logger.info(f"Successfully")
        return order
