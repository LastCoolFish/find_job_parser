from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio.session import AsyncSession

from scrapers.dto.OrderDTO import OrderDTO

from db.engine import request

from db.models.CustomerModel import CustomerModel
from db.models.OrderModel import OrderModel
from logging_config import get_logger

logger = get_logger(__name__)


class OrdersRepository:
    @staticmethod
    @request
    async def get_or_create_customers(entities: list[OrderDTO], session: AsyncSession) -> dict[tuple[str, str], int]:
        """
        When populating the CustomerDTO with data from the database, it is necessary to retrieve the customer IDs or create them if they do not exist.

        :param entities: list of scrapers.dto.OrderDTO
        :param session: sqlalchemy.ext.asyncio.AsyncSession
        :return: dict  of {(customer.name, customer.platform): customer.id in db}
        """

        logger.info(f"Resolving customer ids for {len(entities)} orders")

        # A dictionary is created using a key composed of the customer's name and the platform, since names may be duplicated across different platforms.
        customers = {(entity.customer.name, entity.customer.platform): {"href": entity.customer.href}
                     for entity in entities}

        # A database query is being executed to retrieve customers by name.
        existing = await session.execute(
            select(CustomerModel).where(CustomerModel.name.in_(
                map(lambda customer: customer[0], customers.keys())
            ))
        )

        name_to_id = {(customer.name, customer.platform): customer.id for customer in existing.scalars().all()}


        missing = customers.keys() - name_to_id.keys()
        if missing:
            logger.debug(f"Creating {len(missing)} new customers: {missing}")
            new_customers = [CustomerModel(name=n, platform=plat, **customers[(n, plat)]) for n, plat in missing]
            # Adding all customers in a single transaction
            session.add_all(new_customers)
            await session.flush()
            name_to_id.update({(customer.name, customer.platform): customer.id for customer in new_customers})

        logger.info(f"Successfully resolved {len(name_to_id)} customers")
        return name_to_id

    @staticmethod
    @request
    async def save_orders(
            entities: list[OrderDTO],
            customer_ids: dict[tuple[str, str], int],
            session: AsyncSession,
    ) -> None:
        """
        Saves the passed OrderDTO to the database; customer identifier data is required.

        :param entities: list of scrapers.dto.OrderDTO
        :param customer_ids: dict of customer id, key is tuple of customer.name and customer.platform
        :param session: sqlalchemy.ext.asyncio.AsyncSession
        :return: None
        """

        logger.info(f"Saving {len(entities)} orders")

        # OrderDTO are collected into a single model with all the data
        rows = [
            {
                "name": entity.name,
                "description": entity.description,
                "price": entity.price,
                "publication_timestamp": entity.publication_timestamp,
                "platform": entity.platform,
                "platform_id": entity.order_id,
                "customer_id": customer_ids[(entity.customer.name, entity.customer.platform)],
            }
            for entity in entities
        ]

        # Inserting all orders in a single transaction
        stmt = insert(OrderModel).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["platform", "platform_id"]
        )
        await session.execute(stmt)

        logger.info("Successfully")
